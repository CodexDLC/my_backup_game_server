import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, select

load_dotenv()
sync_url = os.getenv("DATABASE_URL").replace("+asyncpg", "")
engine = create_engine(sync_url)
meta = MetaData()
meta.reflect(bind=engine)

os.makedirs("data_exports", exist_ok=True)

for table in meta.sorted_tables:
    cols = [c.name for c in table.columns]
    path = os.path.join("data_exports", f"{table.name}.sql")
    with engine.connect() as conn, open(path, "w", encoding="utf-8") as f:
        rows = conn.execute(select(table)).all()
        for row in rows:
            vals = []
            for v in row:
                if v is None:
                    vals.append("NULL")
                elif isinstance(v, str):
                    escaped = v.replace("'", "''")
                    vals.append(f"'{escaped}'")
                else:
                    vals.append(str(v))
            schema = f"{table.schema}." if table.schema else ""
            f.write(f"INSERT INTO {schema}{table.name} ({', '.join(cols)}) VALUES ({', '.join(vals)});\n")
