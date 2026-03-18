import json
import os
try:
    from . import paths
    from .logger import logger
except ImportError:
    from app.utils import paths, logger

def load_json(path):
    if not path.exists():
        return {}
    try:
        if not path.exists() or path.stat().st_size == 0:
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки {path.name}: {e}")
        return {}

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка сохранения {path.name}: {e}")

def load_config():
    """Загружает все части конфигурации в единый словарь."""
    auth = load_json(paths.AUTH_JSON)
    filters = load_json(paths.FILTERS_JSON)
    repos = get_tracking_list()
    
    return {
        **auth,
        **filters,
        "github_tracking": repos
    }

def get_tracking_list():
    """Возвращает список отслеживаемых репозиториев из repos.json."""
    return load_json(paths.REPOS_JSON)

def save_tracking_list(repos):
    """Сохраняет список отслеживаемых репозиториев."""
    save_json(paths.REPOS_JSON, repos)

def get_web_auth():
    """Возвращает логин и пароль для веб-интерфейса."""
    return load_json(paths.WEB_AUTH_JSON)

def get_github_token():
    """Возвращает токен GitHub из auth.json."""
    auth = load_json(paths.AUTH_JSON)
    return auth.get("github_token")

def get_packages_arch():
    """Возвращает список целевых архитектур из filters.json."""
    filters = load_json(paths.FILTERS_JSON)
    return filters.get("packages_arch", ["all"])

def ensure_default_configs():
    """Создает файлы конфигурации с настройками по умолчанию или мигрирует из старого config.json."""
    # 1. Сначала проверяем старый конфиг для миграции
    old_config_path = paths.DATA_DIR / "config.json"
    old_data = load_json(old_config_path) if old_config_path.exists() else {}
    
    defaults = {
        paths.AUTH_JSON: {
            "github_token": old_data.get("github_token", "")
        },
        paths.WEB_AUTH_JSON: {
            "username": "admin", 
            "password": "admin"
        },
        paths.REPOS_JSON: old_data.get("github_tracking", []),
        paths.FILTERS_JSON: {
            "packages_arch": old_data.get("packages_arch", ["all"]), 
            "update_interval_hours": old_data.get("update_interval_hours", 12)
        }
    }
    
    for path, data in defaults.items():
        if not path.exists() or path.stat().st_size == 0:
            save_json(path, data)
            logger.info(f"Инициализирован конфигурационный файл: {path.name}")

if __name__ == "__main__":
    ensure_default_configs()
    print("Config Auth:", load_json(paths.AUTH_JSON))
    print("Tracking:", get_tracking_list())
