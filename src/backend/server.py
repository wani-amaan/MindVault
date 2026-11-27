import multiprocessing
import uvicorn
from src.backend.main import app


def main() -> None:
    """Entrypoint for the standalone MindVault backend executable."""
    multiprocessing.freeze_support()
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
