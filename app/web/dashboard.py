from functools import wraps
from flask import Flask, render_template, jsonify, request, Response
try:
    from ..utils import paths, config, logger
    from ..services import sync, publisher
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from app.utils import paths, logger, config
    from app.services import sync, publisher

app = Flask(__name__)

def check_auth(username, password):
    """Проверяет соответствие логина и пароля."""
    auth_data = config.get_web_auth()
    return username == auth_data.get('username') and password == auth_data.get('password')

def authenticate():
    """Отправляет 401 ответ, вызывающий окно ввода пароля."""
    return Response(
    'Нужна авторизация.\n'
    'Пожалуйста, введите логин и пароль.', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@requires_auth
def index():
    return render_template('index.html')

@app.route('/packages/<path:filename>')
@app.route('/<path:filename>')
def serve_packages(filename):
    from flask import send_from_directory
    # Сначала ищем в PACKAGES_DIR
    if (paths.PACKAGES_DIR / filename).exists():
        return send_from_directory(paths.PACKAGES_DIR, filename)
    # Если не нашли, возвращаем 404
    return "Not Found", 404

@app.route('/public.pem')
def serve_public_key():
    from flask import send_from_directory
    return send_from_directory(paths.KEYS_DIR, "public.pem")

@app.route('/api/config', methods=['GET', 'POST'])
@requires_auth
def handle_config():
    if request.method == 'POST':
        data = request.json
        
        # 1. GitHub Token (auth.json)
        if 'github_token' in data:
            config.save_json(paths.AUTH_JSON, {"github_token": data['github_token']})
            
        # 2. Tracking List (repos.json)
        if 'github_tracking' in data:
            config.save_json(paths.REPOS_JSON, data['github_tracking'])
            
        # 3. Filters & Interval (filters.json)
        filters = {}
        if 'packages_arch' in data:
            filters['packages_arch'] = data['packages_arch']
        if 'update_interval_hours' in data:
            filters['update_interval_hours'] = data['update_interval_hours']
        
        if filters:
            config.save_json(paths.FILTERS_JSON, filters)
            
        return jsonify({"status": "success"})
    return jsonify(config.load_config())

@app.route('/api/packages')
@requires_auth
def list_packages():
    import os
    import datetime
    packages = []
    if paths.PACKAGES_DIR.exists():
        for item in sorted(paths.PACKAGES_DIR.iterdir()):
            if item.is_file():
                stat = item.stat()
                packages.append({
                    "name": item.name,
                    "size": f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1024*1024 else f"{stat.st_size / (1024*1024):.1f} MB",
                    "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "url": f"/packages/{item.name}"
                })
    return jsonify(packages)

@app.route('/api/stats')
@requires_auth
def get_stats():
    import os
    import datetime
    total_size = 0
    count = 0
    last_update = "Никогда"
    
    if paths.PACKAGES_DIR.exists():
        for item in paths.PACKAGES_DIR.iterdir():
            if item.is_file() and item.name.endswith('.apk'):
                count += 1
                stat = item.stat()
                total_size += stat.st_size
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                if last_update == "Никогда" or mtime > datetime.datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S'):
                    last_update = mtime.strftime('%Y-%m-%d %H:%M:%S')
    
    size_str = f"{total_size / 1024:.1f} KB" if total_size < 1024*1024 else f"{total_size / (1024*1024):.1f} MB"
    
    return jsonify({
        "packages_count": count,
        "total_size": size_str,
        "last_update": last_update
    })

@app.route('/api/logs')
@requires_auth
def get_logs():
    log_file = paths.LOGS_DIR / "app.log"
    if not log_file.exists():
        return jsonify({"logs": "Лог-файл пуст."})
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return jsonify({"logs": "".join(lines[-50:])})
    except Exception as e:
        return jsonify({"logs": f"Ошибка чтения логов: {e}"})

@app.route('/api/update', methods=['POST'])
@requires_auth
def trigger_full_update():
    logger.logger.info("Запуск полного обновления (Sync + Publish) через UI.")
    import threading
    threading.Thread(target=sync.run_full_update).start()
    return jsonify({"status": "update_started"})

# Оставляем старые роуты для совместимости, но помечаем логом
@app.route('/api/sync', methods=['POST'])
@requires_auth
def trigger_sync():
    logger.logger.info("Запуск только синхронизации (Sync) через UI.")
    import threading
    threading.Thread(target=sync.run_sync_all).start()
    return jsonify({"status": "sync_started"})

@app.route('/api/publish', methods=['POST'])
@requires_auth
def trigger_publish():
    logger.logger.info("Запуск только публикации (Publish) через UI.")
    import threading
    threading.Thread(target=publisher.publish_repo).start()
    return jsonify({"status": "publish_started"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
