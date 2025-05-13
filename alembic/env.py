import glob
import os
import sys
from dotenv import load_dotenv
from logging.config import fileConfig
import sqlalchemy as sa
from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Пути ──
here = os.path.dirname(__file__)
project_root = os.path.dirname(here)
sys.path.insert(0, project_root)    # делаем game_server доступным
SEEDS_DIR = os.path.join(project_root, "game_server", "database", "schemas", "seeds")

# ── Подгружаем .env ──
load_dotenv(os.path.join(project_root, ".env"))

# ── Конфиг Alembic ──
config = context.config
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
fileConfig(config.config_file_name)

# ── Метадата моделей ──
from game_server.database.models.models import Base
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

            # ── Подгружаем сиды ──
            for path in sorted(glob.glob(os.path.join(SEEDS_DIR, "*.sql"))):
                sql = open(path, encoding="utf-8").read()
                connection.execute(sa.text(sql))
