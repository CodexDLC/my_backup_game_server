import os
import glob
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import sqlalchemy as sa

# ─── Импорт глобального логгера ───────────────────────────────────────────────
sys.path.insert(0, ".")

from game_server.services.logging.logging_setup import logger


# ─── Загрузка переменных окружения ─────────────────────────────────────────────
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL").replace("asyncpg", "psycopg2")

# ─── Подключение к базе данных ─────────────────────────────────────────────────
engine = create_engine(DATABASE_URL)

# ─── Сканирование SQL-файлов во всех подпапках схем ────────────────────────────
SCHEMA_DIR = os.path.abspath("game_server/database/schemas")
sql_files = sorted(glob.glob(os.path.join(SCHEMA_DIR, "**", "*.sql"), recursive=True))

def ensure_tracking_table(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS  applied_sql_files (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT now()
        );
    """))
    logger.debug("📋 Таблица applied_sql_files проверена/создана.")

def get_applied_files(conn):
    result = conn.execute(text("SELECT filename FROM applied_sql_files"))
    applied = set(row[0] for row in result.fetchall())
    logger.debug(f"📁 Уже применённых SQL-файлов: {len(applied)}")
    return applied

def apply_sql_file(conn, filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            sql = f.read()
        conn.execute(text(sql))
        conn.execute(text("""
            INSERT INTO applied_sql_files (filename, applied_at)
            VALUES (:f, :t)
        """), {"f": filepath, "t": datetime.utcnow()})
        table_name = os.path.splitext(os.path.basename(filepath))[0]
        logger.info(f"✅ Таблица `{table_name}` успешно применена.")
    except Exception as e:
        logger.error(f"❌ Ошибка при применении файла: {filepath}")
        logger.error(f"🔻 Причина: {e}")

def main():
    logger.info("🚀 Запуск загрузчика SQL-схем...")
    with engine.begin() as conn:
        ensure_tracking_table(conn)
        applied = get_applied_files(conn)
        to_apply = [f for f in sql_files if f not in applied]

        if not to_apply:
            logger.success("🎉 Все SQL-файлы уже применены.")
            return

        for path in to_apply:
            apply_sql_file(conn, path)

if __name__ == "__main__":
    main()
