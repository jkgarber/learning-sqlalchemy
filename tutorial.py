from sqlalchemy import create_engine
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='tutorial.log', level=logging.INFO)

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

logger.info("Getting a Connection")
with engine.connect() as conn:
    result = conn.execute(text("select 'hello world'"))
    print(result.all())
    
logger.info("Committing Changes: commit as you go")
with engine.connect() as conn:
    conn.execute(text("CREATE TABLE some_table (x int, y int)"))
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 1, "y": 1}, {"x": 2, "y": 4}],
    )
    conn.commit()

logger.info("Committing Changes: begin once")
with engine.begin() as conn:
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 6, "y": 8}, {"x": 9, "y": 10}],
    )

logger.info("Fetching Rows")
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table"))
    for row in result:
        print(f"x: {row.x} y: {row.y}")

logger.info("Sending Parameters")
with engine.connect() as conn:
    result = conn.execute(text("SELECT x, y FROM some_table WHERE y > :y"), {"y": 2})
    for row in result:
        print(f"x: {row.x} y: {row.y}")

logger.info("Sending Multiple Parameters")
with engine.connect() as conn:
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 11, "y": 12}, {"x": 13, "y": 14}]
    )
    conn.commit()
