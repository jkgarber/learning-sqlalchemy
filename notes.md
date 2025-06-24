# Learning SQLAlchemy

Following the official [SQLAlchemy Unified Tutorial — SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/tutorial/index.html)

## Installation ([Source](https://docs.sqlalchemy.org/en/20/intro.html))

In a Python venv: `pip install sqlalchemy`

## Establishing Connectivity - the Engine ([Source](https://docs.sqlalchemy.org/en/20/tutorial/engine.html))

Every SQLAlchemy application that connects to a database needs to use an `Engine`. The `Engine` is created by using the `create_engine()` function:

```py
from sqlalchemy import create_engine
engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
```

The string URL is composed of:
- The kind of database: `sqlite`
- The DBAPI: `pysqlite`
- The database location: `/:memory:`

Passing `echo=True` ensures that the `Engine` will log all of the SQL it emits to a Python logger that will write to standard out.

## Working with Transactions and the DBAPI ([Source](https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html))

As we have yet to introduce the SQLAlchemy Expression Language that is the primary feature of SQLAlchemy, we’ll use a simple construct within this package called the `text()` construct, to write SQL statements as textual SQL. Rest assured that textual SQL is the exception rather than the rule in day-to-day SQLAlchemy use, but it’s always available.

```py
from sqlalchemy import text
```

### Getting a Connection

The purpose of the `Engine` is to connect to the database by providing a `Connection` object. Because the `Connection` creates an open resource against the database, we want to limit our use of this object to a specific context. The best way to do that is with a Python context manager, also known as the `with` statement.

```py
with engine.connect() as conn:
	result = conn.execute(text("select 'hello world'"))
	print(result.all())
```

### Committing Changes

We can change our example above to create a table, insert some data and then commit the transaction using the `Connection.commit()` method, inside the block where we have the `Connection` object:

```py
with engine.connect() as conn:
	conn.execute(text("CREATE TABLE some_table (x int, y int)"))
	conn.execute(
		text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
		[{"x": 1, "y": 1}, {"x": 2, "y": 4}],
	)
	conn.commit()
```

After this, we can continue to run more SQL statements and call `Connection.commit()` again for those statements. SQLAlchemy refers to this style as **commit as you go**.
