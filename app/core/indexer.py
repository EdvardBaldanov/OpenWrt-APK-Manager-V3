import subprocess
import os
import json
import re
from pathlib import Path
try:
    from ..utils import paths, logger
except ImportError:
    from app.utils import paths, logger

def extract_meta_from_filename(filename: str):
    """Извлекает имя и версию из стандартного имени файла OpenWrt APK."""
    # Примеры: amneziawg-tools_v25.12.0_x86_64_x86_64.apk, luci-app-podkop-0.7.14-r1.apk
    # Обычно разделитель _ или - перед версией.
    match = re.match(r"^(.+?)[_-](v?\d+\.[\d\.\-r]+)", filename)
    if match:
        return match.group(1), match.group(2).rstrip('.')
    return filename.split('_')[0], "unknown"

def generate_index_json(apk_dir: Path, output_path: Path):
    """Генерирует index.json со списком пакетов и версий."""
    logger.logger.info(f"Генерация index.json в {apk_dir}...")
    packages = {}
    for apk in apk_dir.glob("*.apk"):
        name, ver = extract_meta_from_filename(apk.name)
        packages[name] = ver
    
    data = {
        "version": 2,
        "architecture": "x86_64", # Можно брать из конфига
        "packages": packages
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_apk_index(apk_dir: Path, private_key: Path = None):
    """Создает стандартизированные файлы индекса (packages.adb, index.json и т.д.)."""
    logger.logger.info(f"Создание стандартизированного индекса в {apk_dir}...")
    
    adb_path = apk_dir / "packages.adb"
    
    # 1. Генерация packages.adb
    cmd = [
        str(paths.APK_BIN),
        "mkndx",
        "--output", str(adb_path),
        "--allow-untrusted",
    ]
    
    apk_files = list(apk_dir.glob("*.apk"))
    if not apk_files:
        logger.logger.warning(f"Нет APK файлов для индексации в {apk_dir}")
        return
        
    cmd.extend([str(apk) for apk in apk_files])
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.logger.info(f"Бинарный индекс создан: {adb_path}")
        
        # 2. Подпись (packages.adb.sig) через Python cryptography (так как adbsign --output не работает)
        if private_key and private_key.exists():
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives import serialization
            
            with open(private_key, "rb") as f:
                key_data = serialization.load_pem_private_key(f.read(), password=None)
            
            with open(adb_path, "rb") as f:
                adb_data = f.read()
            
            signature = key_data.sign(adb_data, ec.ECDSA(hashes.SHA256()))
            
            sig_path = apk_dir / "packages.adb.sig"
            with open(sig_path, "wb") as f:
                f.write(signature)
            logger.logger.info(f"Бинарная подпись создана: {sig_path}")
            
            # 3. ASCII Подпись (packages.adb.asc) - в формате Base64 (аналог armor)
            import base64
            asc_path = apk_dir / "packages.adb.asc"
            with open(asc_path, "w") as f:
                f.write("-----BEGIN APK SIGNATURE-----\n")
                f.write(base64.b64encode(signature).decode('utf-8'))
                f.write("\n-----END APK SIGNATURE-----\n")
            logger.logger.info(f"ASCII подпись создана: {asc_path}")
        
        # 4. Генерация index.json
        generate_index_json(apk_dir, apk_dir / "index.json")
        
    except subprocess.CalledProcessError as e:
        logger.logger.error(f"Ошибка при создании индекса: {e.stderr}")
        raise
