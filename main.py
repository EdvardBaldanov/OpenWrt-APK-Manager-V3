import argparse
from app.utils import paths, logger, config
from app.web import dashboard

def main():
    parser = argparse.ArgumentParser(description="OpenWrt APK v3 Manager")
    parser.add_argument("--port", type=int, default=8080, help="Port for the web dashboard")
    parser.add_argument("--sync", action="store_true", help="Run sync and exit")
    parser.add_argument("--publish", action="store_true", help="Run publish and exit")
    
    args = parser.parse_args()
    
    # Инициализация
    paths.ensure_folders()
    config.ensure_default_configs()
    
    if args.sync:
        from app.services import sync
        sync.run_sync_all()
    elif args.publish:
        from app.services import publisher
        publisher.publish_repo()
    else:
        from app.services import scheduler
        scheduler.start_scheduler()
        
        logger.logger.info(f"Запуск веб-интерфейса на порту {args.port}...")
        dashboard.app.run(host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
