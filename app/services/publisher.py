from pathlib import Path
try:
    from ..utils import paths, logger, config
    from ..core import indexer, signer
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from app.utils import paths, logger, config
    from app.core import indexer, signer

def publish_repo():
    """Выполняет индексацию и подпись единого репозитория."""
    logger.logger.info("Начало публикации единого репозитория...")
    
    # Проверка наличия ключей
    priv_key = paths.KEYS_DIR / "private.pem"
    if not priv_key.exists():
        logger.logger.info("Генерация новых ключей P-256...")
        signer.generate_p256_keypair(paths.KEYS_DIR)
    
    if paths.PACKAGES_DIR.exists():
        logger.logger.info(f"Обработка директории пакетов: {paths.PACKAGES_DIR}")
        
        # Индексация (теперь генерирует packages.adb и сопутствующие файлы)
        indexer.create_apk_index(paths.PACKAGES_DIR, private_key=priv_key)
                
    logger.logger.info("Публикация завершена.")

if __name__ == "__main__":
    publish_repo()
