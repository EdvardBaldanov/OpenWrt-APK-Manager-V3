import threading
import time
import datetime
try:
    from ..utils import config, logger
    from . import sync
except ImportError:
    from app.utils import config, logger
    from app.services import sync

def start_scheduler():
    """Запускает планировщик обновлений в фоновом потоке."""
    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()
    logger.logger.info("Фоновый планировщик обновлений запущен.")

def _scheduler_loop():
    """Основной цикл планировщика."""
    # Ждем немного после старта сервера, прежде чем начать первое планирование
    # (Чтобы не мешать ручному запуску или инициализации)
    time.sleep(10) 
    
    while True:
        try:
            cfg = config.load_config()
            interval = cfg.get("update_interval_hours", 6)
            
            # Логируем следующее время запуска
            next_run = datetime.datetime.now() + datetime.timedelta(hours=interval)
            logger.logger.info(f"Планировщик: Следующее авто-обновление запланировано на {next_run.strftime('%Y-%m-%d %H:%M:%S')} (через {interval} ч.)")
            
            # Ждем интервал
            time.sleep(interval * 3600)
            
            logger.logger.info("Планировщик: Запуск планового обновления репозитория...")
            sync.run_full_update()
            
        except Exception as e:
            logger.logger.error(f"Ошибка в цикле планировщика: {e}")
            time.sleep(60) # При ошибке ждем минуту и пробуем снова
