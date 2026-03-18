import subprocess
import os
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
try:
    from ..utils import paths, logger
except ImportError:
    from app.utils import paths, logger

def generate_p256_keypair(key_dir: Path):
    """Генерирует пару ключей P-256 для APK v3."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Сохранение приватного ключа
    with open(key_dir / "private.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Сохранение публичного ключа
    public_key = private_key.public_key()
    with open(key_dir / "public.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def sign_with_apk(file_path: Path, private_key_path: Path, output_path: Path = None):
    """Подписывает файл (пакет или индекс) с помощью apk adbsign."""
    logger.logger.info(f"Подпись файла {file_path} с помощью apk adbsign...")
    
    cmd = [
        str(paths.APK_BIN),
        "adbsign",
        "--sign-key", str(private_key_path),
    ]
    
    if output_path:
        cmd.extend(["--output", str(output_path)])
        
    cmd.append(str(file_path))
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.logger.info(f"Файл успешно подписан.")
        return True
    except subprocess.CalledProcessError as e:
        logger.logger.error(f"Ошибка при запуске apk adbsign: {e.stderr}")
        return False
