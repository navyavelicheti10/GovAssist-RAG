import os


def load_env_file(file_path: str = ".env") -> None:
    """
    Simple .env loader so the backend can run without extra config code.
    Existing environment variables win over values from the file.
    """
    if not os.path.exists(file_path):
        return

    with open(file_path, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
