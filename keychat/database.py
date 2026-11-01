import sqlite3
import os
import sys


def _app_dir() -> str:
    """Папка приложения: рядом с exe в frozen-режиме, иначе рядом с пакетом."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_DIR = _app_dir()
DB_PATH = os.path.join(APP_DIR, "keychat.db")


def _preview_text(text, msg_type, meta):
    """Короткое отображаемое значение в списке чатов для сообщений разных типов."""
    if msg_type == "sticker":
        return "[Стикер]"
    if msg_type == "file":
        name = ""
        if meta:
            for part in meta.split("|"):
                if part.startswith("name="):
                    name = part[5:]
                    break
        return "[Файл] " + (name or "вложение")
    return text


class Database:
    """SQLite-хранилище: пользователи, настройки, сообщения и чаты."""

    def __init__(self, path=DB_PATH, crypto=None):
        self.path = path
        self.crypto = crypto
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()

    def _create_tables(self):
        c = self.conn
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                avatar_color TEXT NOT NULL DEFAULT '#FF7A1A',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                peer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                last_message TEXT,
                last_seen TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                msg_type TEXT NOT NULL DEFAULT 'text',
                meta TEXT,
                sent_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )
        self._migrate()
        self.conn.commit()

    def _migrate(self):
        """Добавляет колонки msg_type/meta в старые базы (без их потери)."""
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(messages)")}
        if "msg_type" not in cols:
            self.conn.execute(
                "ALTER TABLE messages ADD COLUMN msg_type TEXT NOT NULL DEFAULT 'text'"
            )
        if "meta" not in cols:
            self.conn.execute("ALTER TABLE messages ADD COLUMN meta TEXT")

    # ---------- settings ----------
    def get_setting(self, key, default=None):
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.conn.commit()

    # ---------- users ----------
    def get_user_by_name(self, username):
        row = self.conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)
        ).fetchone()
        return dict(row) if row else None

    def create_user(self, username, avatar_color):
        cur = self.conn.execute(
            "INSERT INTO users(username, avatar_color) VALUES(?, ?)",
            (username, avatar_color),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_username(self, user_id, new_username):
        self.conn.execute(
            "UPDATE users SET username = ? WHERE id = ?", (new_username, user_id)
        )
        self.conn.commit()

    def update_avatar_color(self, user_id, color):
        self.conn.execute(
            "UPDATE users SET avatar_color = ? WHERE id = ?", (color, user_id)
        )
        self.conn.commit()

    def list_users(self):
        return [
            dict(r)
            for r in self.conn.execute(
                "SELECT * FROM users ORDER BY username COLLATE NOCASE"
            )
        ]

    # ---------- messages ----------
    def send_message(self, chat_id, sender_id, text, msg_type="text", meta=None):
        stored = self.crypto.encrypt_text(text) if self.crypto and msg_type == "text" else text
        cur = self.conn.execute(
            "INSERT INTO messages(chat_id, sender_id, text, msg_type, meta) "
            "VALUES(?, ?, ?, ?, ?)",
            (chat_id, sender_id, stored, msg_type, meta),
        )
        display = _preview_text(text, msg_type, meta)
        self.conn.execute(
            "UPDATE chats SET last_message = ?, last_seen = datetime('now', 'localtime') "
            "WHERE id = ?",
            (display, chat_id),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM messages WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return self._decrypt_message(dict(row))

    def get_history(self, chat_id, limit=200):
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        ).fetchall()
        return [self._decrypt_message(dict(r)) for r in rows][::-1]

    def _decrypt_message(self, m):
        if m["msg_type"] == "text" and self.crypto:
            m["text"] = self.crypto.decrypt_text(m["text"])
        return m

    def clear_history(self, chat_id):
        self.conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        self.conn.execute(
            "UPDATE chats SET last_message = NULL WHERE id = ?", (chat_id,)
        )
        self.conn.commit()

    def clear_all_messages(self):
        self.conn.execute("DELETE FROM messages")
        self.conn.execute("UPDATE chats SET last_message = NULL, last_seen = NULL")
        self.conn.commit()

    # ---------- chats ----------
    def get_or_create_chat(self, peer_id):
        row = self.conn.execute(
            "SELECT id FROM chats WHERE peer_id = ?", (peer_id,)
        ).fetchone()
        if row:
            return row["id"]
        cur = self.conn.execute("INSERT INTO chats(peer_id) VALUES(?)", (peer_id,))
        self.conn.commit()
        return cur.lastrowid

    def list_chats(self):
        rows = self.conn.execute(
            """
            SELECT c.id, c.last_message, c.last_seen,
                   u.id AS peer_id, u.username, u.avatar_color
            FROM chats c
            JOIN users u ON u.id = c.peer_id
            ORDER BY COALESCE(c.last_seen, '') DESC, c.id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def add_friend(self, username):
        user = self.get_user_by_name(username)
        if not user:
            return None
        self.get_or_create_chat(user["id"])
        return user

    def existing_usernames(self):
        return [u["username"] for u in self.list_users()]

    def close(self):
        self.conn.close()