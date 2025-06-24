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

We can create a table, insert some data and then commit the transaction using the `Connection.commit()` method, inside the block where we have the `Connection` object:

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

The default behavior of the Python DBAPI is that a transaction is always in progress. However, we can declare our “connect” block to be a transaction block up front. To do this, we use the `Engine.begin()` method to get the connection, rather than the `Engine.connect()` method. This method will enclose everything inside of a transaction with either a COMMIT at the end if the block was successful, or a ROLLBACK if an exception was raised.

```py
with engine.begin() as conn:
	conn.execute(
		text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
		[{"x": 6, "y": 8}, {"x": 9, "y": 10}],
	)
```

This style is known as **begin once**. You should mostly prefer this style because it’s shorter and shows the intention of the entire block up front. However, in this tutorial we’ll use “commit as you go” style as it’s more flexible for demonstration purposes.

### Basics of Statement Execution

In this section we’ll illustrate more closely the mechanics and interactions of `Connection.execute()`, `text()`, and `Result`.

#### Fetching Rows

We’ll first illustrate the `Result` object more closely by making use of the rows we’ve inserted previously, running a textual SELECT statement on the table we’ve created:

```py
with engine.connect() as conn:
	result = conn.execute(text("SELECT x, y FROM some_table"))
	for row in result:
		print(f"x: {row.x} y:{row.y}")
```

`Conn.execute()` returned a called `Result` object representing an iterable object of result rows. The `Result.all()` method returns a list of all the `Row` objects. The `Row` objects themselves are intended to act like Python named tuples. Below we illustrate a variety of ways to access rows.

- **Tuple Assignment**: Assign variables to each row positionally as they are received:
	```py
	result = con.execute(text("select x, y from some_table"))
	for x, y in result:
		...
	```
- **Integer Index**: Tuples are Python sequences, so regular integer access is available too:
	```py
	result = conn.execute(text("select x, y from some_table"))
	for row in result:
		x = row[0]
	```
- **Attribute Name**: As these are Python named tuples, the tuples have dynamic attribute names matching the names of each column.
	```py
	result = conn.execute(text("select x, y from some_table"))
	for row in result:
		y = row.y
	```
- **Mapping Access**: The Result may be transformed into a `MappingResult` object using the `Result.mappings()` modifier; this is a result object that yields read-only dictionary-like `RowMapping` objects rather than `Row` objects:
	```py
	result = conn.execute(text("select x, y from some_table"))
	for dict_row in result.mappings():
		x = dict_row["x"]
		y = dict_row["y"]
	```

#### Sending Parameters

The `Connection.execute()` method accepts parameters which are known as bound parameters. For example, say we wanted to limit our SELECT statement only to rows where the “y” value were greater than a certain value. The `text()` construct accepts these using a colon format “`:y`”. The actual value for “`:y`” is then passed as the second argument to `Connection.execute()` in the form of a dictionary:

```py
with engine.connect() as conn:
	result = conn.execute(text("SElECT x, y FROM some_table WHERE y > :y"), {"y": 2})
	for row in result:
		print(f"x: {row.x} y: {row.y}")
```

In the logged SQL output the bound parameter `:y` was converted into a question mark because the SQLite database driver uses a format called “qmark parameter style”. This is most famously known as how to avoid SQL injection attacks when the data is untrusted. However it also allows the SQLAlchemy dialects and/or DBAPI to correctly handle the incoming input for the backend.

#### Sending Multiple Parameters

For DML statements such as “INSERT”, “UPDATE” and “DELETE”, we can send multiple parameter sets to the `Connection.execute()` method by passing a list of dictionaries instead of a single dictionary, which indicates that the single SQL statement should be invoked multiple times, once for each parameter set. This style of execution is known as executemany:

```py
with engine.connect() as conn:
	conn.execute(
		text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
		[{"x": 11, "y": 12}, {"x": 13, "y": 14}],
	)
	conn.commit()
```

A key behavioral difference between “execute” and “executemany” is that the latter doesn’t support returning of result rows, even if the statement includes the RETURNING clause. The one exception to this is when using a Core `insert()` construct, introduced later in this tutorial.
