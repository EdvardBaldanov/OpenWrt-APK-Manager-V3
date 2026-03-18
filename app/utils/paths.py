import os
import sys
from pathlib import Path

def get_base_dir() -> Path:
    """Определяет корневую директорию проекта."""
    # Если запущено как скомпилированный бинарник (Nuitka/PyInstaller)
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    # Если запущен исходный код
    return Path(__file__).resolve().parent.parent.parent

# Основные пути
BASE_DIR = get_base_dir()
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
BIN_DIR = BASE_DIR / "bin"

# Поддиректории данных
KEYS_DIR = DATA_DIR / "keys"
PACKAGES_DIR = DATA_DIR / "packages"
LOGS_DIR = DATA_DIR / "logs"

# Файлы конфигурации
AUTH_JSON = DATA_DIR / "auth.json"
WEB_AUTH_JSON = DATA_DIR / "web_auth.json"
REPOS_JSON = DATA_DIR / "repos.json"
FILTERS_JSON = DATA_DIR / "filters.json"

# Бинарники
APK_BIN = BIN_DIR / "host" / "bin" / "apk"

def ensure_folders():
    """Создает необходимые директории при старте."""
    folders = [KEYS_DIR, PACKAGES_DIR, LOGS_DIR, BIN_DIR]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print(f"BASE_DIR: {BASE_DIR}")
    ensure_folders()
