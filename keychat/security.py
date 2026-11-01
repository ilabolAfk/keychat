import os
import secrets
import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken

# Количество итераций для scrypt-хеша пароля (в меру — быстрый вход, без задержки).
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAXMEM = 256 * 1024 * 1024  # открыто для OpenSSL


def hash_password(password: str) -> str:
    """Возвращает формат 'scrypt$<salt_hex>$<hash_hex>' — соль вшита в хеш."""
    salt = secrets.token_hex(16)
    key = hashlib.scrypt(
        password.encode("utf-8"), salt=bytes.fromhex(salt),
        n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32, maxmem=SCRYPT_MAXMEM,
    )
    return f"scrypt${salt}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Проверяет пароль против хеша, возвращает False для некорректного формата."""
    if not stored or not stored.startswith("scrypt$"):
        return False
    try:
        _, salt_hex, hash_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    actual = hashlib.scrypt(
        password.encode("utf-8"), salt=salt,
        n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32, maxmem=SCRYPT_MAXMEM,
    )
    return hmac.compare_digest(actual, expected)

# Ключ и файлы хранятся рядом с базой, путь выводится из неё, а не хардкодится.
KEY_EXTENSION = ".key"


def _key_path(db_path):
    return db_path + KEY_EXTENSION


class Crypto:
    """Шифрование текста и файлов на основе Fernet (AES-128)."""

    def __init__(self, db_path):
        self.key = self._load_or_create_key(_key_path(db_path))
        self.fernet = Fernet(self.key)

    @staticmethod
    def _load_or_create_key(path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        with open(path, "wb") as f:
            f.write(key)
        return key

    # ---- текстовые сообщения ----
    def encrypt_text(self, text: str) -> str:
        token = self.fernet.encrypt(text.encode("utf-8"))
        return token.decode("ascii")

    def decrypt_text(self, token: str) -> str:
        try:
            return self.fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError, UnicodeDecodeError):
            # В токене может лежать старый открытый текст (до введения шифрования)
            return token

    # ---- файлы ----
    def encrypt_file(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def decrypt_file(self, data: bytes) -> bytes:
        return self.fernet.decrypt(data)


def files_dir_for(db_path: str) -> str:
    """Папка для хранения зашифрованных файлов — выводится из пути к БД."""
    base, _ = os.path.splitext(db_path)
    d = base + "_files"
    os.makedirs(d, exist_ok=True)
    return d


def random_stored_name() -> str:
    return "f_" + secrets.token_hex(16) + ".enc"