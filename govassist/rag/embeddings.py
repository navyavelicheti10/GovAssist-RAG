import json
import logging
import os
import re
from typing import Any, Dict, List

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
TAG_KEYWORDS = {
    "student": [
        "student",
        "students",
        "scholarship",
        "education",
        "school",
        "college",
        "university",
        "learning",
        "tuition",
        "course",
        "internship",
    ],
    "farmer": [
        "farmer",
        "farmers",
        "agriculture",
        "crop",
        "milch",
        "cattle",
        "livestock",
        "animal husbandry",
        "poultry",
        "goat",
        "dairy",
    ],
    "women": [
        "women",
        "woman",
        "girl",
        "girls",
        "widow",
        "mother",
        "female",
        "maternity",
    ],
    "loan": [
        "loan",
        "credit",
        "finance",
        "bank",
        "subsidy",
        "interest subvention",
    ],
    "pension": [
        "pension",
        "old age",
        "retirement",
        "widow pension",
        "social security",
    ],
    "health": [
        "health",
        "medical",
        "treatment",
        "hospital",
        "insurance",
        "wellness",
    ],
    "disability": [
        "disability",
        "disabled",
        "persons with disabilities",
        "differently abled",
    ],
}


def clean_text(value: Any) -> str:
    """Normalize text so embeddings are more consistent."""
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value if item)
    text = str(value)
    text = text.replace("\u200b", " ").replace("\ufeff", " ").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def dedupe_sentences(text: str) -> str:
    """
    Remove obvious repeated sentences.
    This is helpful because the scraped JSON contains duplicated sections.
    """
    normalized = clean_text(text)
    if not normalized:
        return ""

    parts = re.split(r"(?<=[.!?])\s+", normalized)
    seen = set()
    result = []
    for part in parts:
        candidate = clean_text(part)
        if not candidate:
            continue
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return " ".join(result)


def normalize_tags(tags: Any) -> List[str]:
    if not tags:
        return []
    if isinstance(tags, list):
        raw_tags = tags
    else:
        raw_tags = re.split(r"[,/|]", str(tags))

    normalized = []
    seen = set()
    for tag in raw_tags:
        value = clean_text(tag).lower()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def infer_tags_from_text(text: str, category: str = "") -> List[str]:
    combined = f"{clean_text(text)} {clean_text(category)}".lower()
    inferred = []
    for tag, keywords in TAG_KEYWORDS.items():
        if any(keyword in combined for keyword in keywords):
            inferred.append(tag)
    return inferred


def normalize_scheme(raw_scheme: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Clean one scheme record and add search_text for retrieval."""
    scheme_name = clean_text(raw_scheme.get("scheme_name"))
    category = clean_text(raw_scheme.get("category"))
    description = dedupe_sentences(raw_scheme.get("description", ""))
    eligibility = dedupe_sentences(raw_scheme.get("eligibility", ""))
    benefits = dedupe_sentences(raw_scheme.get("benefits", ""))
    application_process = dedupe_sentences(raw_scheme.get("application_process", ""))
    explicit_tags = normalize_tags(raw_scheme.get("tags", []))
    inferred_tags = infer_tags_from_text(
        " ".join([scheme_name, description, eligibility, benefits, application_process]),
        category=category,
    )
    merged_tags = normalize_tags(explicit_tags + inferred_tags)

    scheme = {
        "id": index,
        "scheme_name": scheme_name,
        "category": category,
        "description": description,
        "eligibility": eligibility,
        "benefits": benefits,
        "documents_required": [
            clean_text(item)
            for item in raw_scheme.get("documents_required", [])
            if clean_text(item)
        ],
        "application_process": application_process,
        "official_link": clean_text(raw_scheme.get("official_link")),
        "tags": merged_tags,
    }

    search_text = " | ".join(
        part
        for part in [
            scheme["scheme_name"],
            scheme["category"],
            scheme["description"],
            scheme["eligibility"],
            scheme["benefits"],
            " ".join(scheme["tags"]),
        ]
        if part
    )
    scheme["search_text"] = clean_text(search_text)
    return scheme


def load_schemes(file_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Scheme data file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        raw_data = json.load(file)

    if not isinstance(raw_data, list):
        raise ValueError("Scheme JSON must contain a list of scheme objects.")

    schemes = [normalize_scheme(item, index) for index, item in enumerate(raw_data)]
    logger.info("Loaded %s schemes from %s", len(schemes), file_path)
    return schemes


class EmbeddingService:
    """Handles text embeddings using the BGE model."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self.model_name = model_name
        logger.info("Loading embedding model: %s", model_name)
        self.model = SentenceTransformer(model_name)

    @property
    def vector_size(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return vectors.tolist()

    def embed_query(self, query: str) -> List[float]:
        query_text = BGE_QUERY_PREFIX + clean_text(query)
        vector = self.model.encode(
            query_text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vector.tolist()
