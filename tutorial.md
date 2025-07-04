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

### Executing with an ORM Session

The fundamental transactional / database interactive object when using the ORM is called the `Session`. This object is used in a manner very similar to that of the `Connection`. It refers to a `Connection` internally which it uses to emit SQL. The `Session` has a few different creational patterns, but here we will illustrate the most basic one that tracks exactly with how the `Connection` is used.

```py
from sqlalchemy.orm import Session

stmt = text("SELECT x, y FROM some_table WHERE y > :y ORDER BY x, y")
with Session(engine) as session:
	result = session.execute(stmt, {"y": 6})
	for row in result:
		print(f"x: {row.x} y: {row.y})
```

Also, like the `Connection`, the `Session` features “commit as you go” behavior using the `Session.commit()` method:

```py
with Session(engine) as session:
	result = session.execute(
		text("UPDATE some_table SET y=:y WHERE x=:x"),
		[{"x": 9, "y": 11}, {"x": 13, "y": 15}],
	)
	session.commit()
```

Note: The `Session` doesn’t hold onto the `Connection` object after it ends the transaction. It gets a new `Connection` from the `Engine` the next time it needs to execute SQL against the database.

## Working with Database Metadata ([Source](https://docs.sqlalchemy.org/en/20/tutorial/metadata.html))

The central element of both SQLAlchemy Core and ORM is the SQL Expression Language which allows for fluent, composable construction of SQL queries. The most common foundational objects for database metadata in SQLAlchemy are known as `MetaData`, `Table`, and `Column`.

### Setting Up MetaData with Table Objects

In SQLAlchemy, the database “table” is ultimately represented by a Python object similarly named `Table`. `Table` objects are constructed programmatically, either directly, or indirectly by using ORM Mapped classes (described later).

We always start out with a collection that will be where we place our tables known as the MetaData object:
```py
from sqlalchemy import MetaData
metadata_obj = MetaData()
```

When not using ORM Declarative models at all, we construct each `Table` object directly, typically assigning each to a variable that will be how we will refer to the table in application code:
```py
from sqlalchemy import Table, Column, Integer, String
user_table = Table(
	"user_account",
	metadata_obj,
	Column("id", Integer, primary_key=True),
	Column("name", String(30)),
	Column("fullname", String),
)
```

We can now use the `user_table` Python variable to refer to the `user_account` table in the database. The `Table` construct has a resemblance to a SQL CREATE TABLE statement.

#### Components of `Table`

- `Table` - represents a database table and assigns itself to a `MetaData` collection.
- `Column` - represents a column in a database table, and assigns itself to a `Table` object. The `Column` usually includes a string name and a type object. The collection of `Column` objects in terms of the parent `Table` are typically accessed via an associative array located at `Table.c`:
	```py
	user_table.c.name
	# Column('name', String(length=30), table=<user_account>)

	user_table.c.keys()
	# ['id', 'name', 'fullname']
	```
- `Integer`, `String` - these classes represent SQL datatypes and can be passed to a `Column` with or without necessarily being instantiated.

#### Declaring Simple Constraints

The `Column.primary_key` parameter is a shorthand technique of indicating that this `Column` should be part of the primary key for this table. The primary key itself is represented by the `PrimaryKeyConstraint` construct, which we can see on the `Table.primary_key` attribute on the `Table` object:
```py
user_table.primary_key
# PrimaryKeyConstraint(Column('id', Integer(), table=<user_account>, primary_key=True, nullable=False))
```

Below we declare a second table `address` that will have a foreign key constraint referring to the `user` table:
```py
from sqlalchemy import ForeignKey
address_table = Table(
	"address",
	metadata_obj,
	Column("id", Integer, primary_key=True),
	Column("user_id", ForeignKey("user_account.id"), nullable=False),
	Column("email_address", String, nullable=False),
)
```

When using the `ForeignKey` object within a `Column` definition, we can omit the datatype for that `Column`; it is automatically inferred from that of the related column, in the above example the `Integer` datatype of the `user_account.id` column. The table above also features a third kind of constraint, which in SQL is the “NOT NULL” constraint, indicated using the `Column.nullable` parameter.

#### Emitting DDL to the Database

We'll emit CREATE TABLE statements, or DDL, to our SQLite database by invoking the `MetaData.create_all()` method on our `MetaData`, sending it the `Engine` that refers to the target database:

```py
metadata_obj.create_all(engine)
```

The DDL create process above includes some SQLite-specific PRAGMA statements that test for the existence of each table before emitting a CREATE. The create process also takes care of emitting CREATE statements in the correct order. In more complicated dependency scenarios the FOREIGN KEY constraints may also be applied to tables after the fact using ALTER.

The `MetaData` object also features a `MetaData.drop_all()` method that will emit DROP statements in the reverse order as it would emit CREATE in order to drop schema elements. Overall, the CREATE / DROP feature of `MetaData` is useful for test suites, small and/or new applications, and applications that use short-lived databases. For management of an application database schema over the long term however, a schema management tool such as Alembic, which builds upon SQLAlchemy, is likely a better choice, as it can manage and orchestrate the process of incrementally altering a fixed database schema over time as the design of the application changes.
