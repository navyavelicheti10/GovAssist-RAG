import os

import uvicorn

from govassist.api.app import app


if __name__ == "__main__":
    uvicorn.run(
        "govassist.api.app:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
    )
