import logging
import sys
from pathlib import Path
try:
    from . import paths
except ImportError:
    import paths

def setup_logger(name: str = "apk_manager"):
    """Настройка логгера с выводом в консоль и файл."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Вывод в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Вывод в файл
    log_file = paths.LOGS_DIR / "app.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
