import base64
import json
import logging
import os
from typing import Dict, Any

import easyocr
from groq import Groq

logger = logging.getLogger(__name__)

class DocumentIntelligence:
    def __init__(self):
        logger.info("Initializing EasyOCR reader for en, hi...")
        # Note for hackathon: EasyOCR model downloads on first use. 
        # Using English for now to keep it fast, add 'hi' or 'ta' for production.
        try:
            self.reader = easyocr.Reader(['en'])
        except Exception as e:
            logger.error(f"Failed to load EasyOCR: {e}")
            self.reader = None
            
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

    def read_with_easyocr(self, image_path: str) -> str:
        """Extracts raw text from an image using EasyOCR."""
        if not self.reader:
            return ""
        try:
            results = self.reader.readtext(image_path, detail=0)
            return " ".join(results)
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return ""

    def read_with_vision_llm(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Extracts structured JSON from an image using Groq Vision API."""
        try:
            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode('utf-8')
                
            response = self.groq_client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
            )
            raw_content = response.choices[0].message.content
            
            # Extract JSON block if surrounded by markdown
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0]
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0]
                
            return json.loads(raw_content.strip())
            
        except Exception as e:
            logger.error(f"Groq Vision LLM error: {e}")
            return {}

    def extract_document_fields(self, image_path: str) -> Dict[str, Any]:
        """
        Master method: Tries OCR first, then routes to Vision LLM for structured extraction.
        This provides a highly faithful extraction of Identity/Income details.
        """
        ocr_text = self.read_with_easyocr(image_path)
        logger.info(f"OCR Extracted {len(ocr_text)} characters.")
        
        prompt = (
            "You are a strict document parser. Analyze the uploaded image (and the accompanying OCR text below if any). "
            "Extract the following fields if present: 'document_type' (e.g., Aadhaar, Income Certificate, PAN), 'name', "
            "'dob', 'income_amount', 'state', 'gender'. "
            "Return ONLY a valid JSON object. No extra text.\n"
            f"OCR Context: {ocr_text}"
        )
        
        extracted_fields = self.read_with_vision_llm(image_path, prompt)
        return extracted_fields

# Singleton instance for easy import
document_intelligence_service = DocumentIntelligence()
