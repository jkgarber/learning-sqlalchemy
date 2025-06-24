Based on [SQLAlchemy Unified Tutorial — SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/tutorial/index.html)

# Installation

1. `source .venv/bin/activate`
2. `pip install sqlalchemy`

[Source](https://docs.sqlalchemy.org/en/20/intro.html)

# Establishing Connectivity - the Engine

Every SQLAlchemy application that connects to a database needs to use an `Engine`. The `Engine` is created by using the `create_engine()` function:

```py
from sqlalchemy import create_engine
engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
```

The string URL is composed of:
- The kind of database: `sqlite`
- The DBAPI: `pysqlite`
- The database location: `/:memory`:

Passing `echo=True` ensures that the `Engine` will log all of the SQL it emits to a Python logger that will write to standard out.

[Source](https://docs.sqlalchemy.org/en/20/tutorial/engine.html)

# Working with Transactions and the DBAPI

[Source](https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html)
