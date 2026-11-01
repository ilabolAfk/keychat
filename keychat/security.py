import os
import secrets

from cryptography.fernet import Fernet, InvalidToken

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