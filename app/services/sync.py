import os
import requests
from github import Github
from pathlib import Path
try:
    from ..utils import paths, config, logger
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from app.utils import paths, config, logger

def sync_repo(repo_full_name: str, target_arch: str):
    """Синхронизирует пакеты из GitHub репозитория для указанной архитектуры."""
    cfg = config.load_config()
    token = cfg.get("github_token")
    g = Github(token) if token else Github()
    
    try:
        repo = g.get_repo(repo_full_name)
        # Получаем только самый свежий релиз
        release = repo.get_latest_release()
        
        # Единая директория для всех пакетов
        arch_dir = paths.PACKAGES_DIR
        arch_dir.mkdir(parents=True, exist_ok=True)
        
        for asset in release.get_assets():
            if asset.name.endswith(".apk"):
                # Гибкое сопоставление архитектуры
                is_match = False
                if target_arch in asset.name:
                    is_match = True
                elif target_arch == "all":
                    # Если ищем 'all', но в имени нет 'all', проверяем нет ли там других архитектур
                    other_archs = ["x86_64", "mips", "arm64", "aarch64", "i386"]
                    if not any(a in asset.name for a in other_archs):
                        is_match = True
                        
                if is_match:
                    dest_path = arch_dir / asset.name
                    if not dest_path.exists():
                        logger.logger.info(f"Загрузка {asset.name} (Latest) из {repo_full_name}...")
                        response = requests.get(asset.browser_download_url)
                        with open(dest_path, "wb") as f:
                            f.write(response.content)
                            
    except Exception as e:
        logger.logger.error(f"Ошибка при синхронизации {repo_full_name}: {e}")

def run_sync_all():
    """Запускает синхронизацию для всех отслеживаемых репозиториев."""
    tracking = config.get_tracking_list()
    cfg = config.load_config()
    archs = cfg.get("packages_arch", ["all"])
    
    logger.logger.info(f"Начало синхронизации. Найдено репозиториев: {len(tracking) if isinstance(tracking, list) else 0}")
    
    if not isinstance(tracking, list):
        logger.logger.warning("Список репозиториев пуст или имеет неверный формат.")
        return

    for item in tracking:
        repo = item.get("repo")
        arch = item.get("arch")
        if repo and arch:
            sync_repo(repo, arch)
        elif repo:
            for a in archs:
                sync_repo(repo, a)
    logger.logger.info("Синхронизация всех репозиториев завершена.")

def run_full_update():
    """Полный цикл: синхронизация всех репозиториев + публикация индекса."""
    from app.services import publisher
    run_sync_all()
    publisher.publish_repo()
