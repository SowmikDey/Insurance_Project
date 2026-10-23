import os
from sqlalchemy import text
from app.core.database import SessionLocal

db = SessionLocal()
res = db.execute(text("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public' AND data_type IN ('character varying', 'text')")).fetchall()
found = []
for t, c in res:
    try:
        cnt = db.execute(text(f'SELECT count(*) FROM "{t}" WHERE "{c}" LIKE :pat'), {'pat': '%market-governance%'}).scalar()
        if cnt > 0:
            found.append((t, c, cnt))
    except Exception as e:
        pass
print("Found occurrences of market-governance:", found)
db.close()
