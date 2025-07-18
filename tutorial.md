# Learning SQLAlchemy

Following the official [SQLAlchemy Unified Tutorial — SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/tutorial/index.html)

## Installation ([Source](https://docs.sqlalchemy.org/en/20/intro.html))

In a uv project: `uv add sqlalchemy`

## Establishing Connectivity - the Engine ([Source](https://docs.sqlalchemy.org/en/20/tutorial/engine.html))

While this subsection is Core-centric, all of the concepts here are relevant to ORM use as well.

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

Note: When using the ORM, the `Engine` is managed by the `Session`. 

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

# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine select 'hello world'
# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine [generated in 0.00017s] ()
# [('hello world',)]
# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine ROLLBACK

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

# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine CREATE TABLE some_table (x int, y int)
# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine [generated in 0.00007s] ()
# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine INSERT INTO some_table (x, y) VALUES (?, ?)
# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine [generated in 0.00007s] [(1, 1), (2, 4)]
# 2025-07-09 15:31:50,941 INFO sqlalchemy.engine.Engine COMMIT

```

After this, we can continue to run more SQL statements and call `Connection.commit()` again for those statements. SQLAlchemy refers to this style as **commit as you go**.

The default behavior of the Python DBAPI is that a transaction is always in progress. However, we can declare our “connect” block to be a transaction block up front. To do this, we use the `Engine.begin()` method to get the connection, rather than the `Engine.connect()` method. This method will enclose everything inside of a transaction with either a COMMIT at the end if the block was successful, or a ROLLBACK if an exception was raised.

```py
with engine.begin() as conn:
	conn.execute(
		text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
		[{"x": 6, "y": 8}, {"x": 9, "y": 10}],
	)

# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine INSERT INTO some_table (x, y) VALUES (?, ?)
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine [cached since 0.0002914s ago] [(6, 8), (9, 10)]
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine COMMIT

```

This style is known as **begin once**. You should mostly prefer this style because it’s shorter and shows the intention of the entire block up front. However, in this tutorial we’ll use “commit as you go” style as it’s more flexible for demonstration purposes.

### Basics of Statement Execution

In this section we’ll illustrate more closely the mechanics and interactions of `Connection.execute()`, `text()`, and `Result`. Most of the content in this section applies equally well to modern ORM use when using the `Session.execute()` method,

#### Fetching Rows

We’ll first illustrate the `Result` object more closely by making use of the rows we’ve inserted previously, running a textual SELECT statement on the table we’ve created:

```py
with engine.connect() as conn:
	result = conn.execute(text("SELECT x, y FROM some_table"))
	for row in result:
		print(f"x: {row.x} y:{row.y}")

# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine SELECT x, y FROM some_table
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine [generated in 0.00006s] ()
# x: 1 y: 1
# x: 2 y: 4
# x: 6 y: 8
# x: 9 y: 10
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine ROLLBACK

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

# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine SELECT x, y FROM some_table WHERE y > ?
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine [generated in 0.00006s] (2,)
# x: 2 y: 4
# x: 6 y: 8
# x: 9 y: 10
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine ROLLBACK

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

# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine INSERT INTO some_table (x, y) VALUES (?, ?)
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine [cached since 0.0009053s ago] [(11, 12), (13, 14)]
# 2025-07-09 15:31:50,942 INFO sqlalchemy.engine.Engine COMMIT

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

# 2025-07-09 15:31:50,975 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-09 15:31:50,975 INFO sqlalchemy.engine.Engine SELECT x, y FROM some_table WHERE y > ? ORDER BY x, y
# 2025-07-09 15:31:50,975 INFO sqlalchemy.engine.Engine [generated in 0.00008s] (6,)
# x: 6 y: 8
# x: 9 y: 10
# x: 11 y: 12
# x: 13 y: 14
# 2025-07-09 15:31:50,975 INFO sqlalchemy.engine.Engine ROLLBACK

```

Also, like the `Connection`, the `Session` features “commit as you go” behavior using the `Session.commit()` method:

```py
with Session(engine) as session:
	result = session.execute(
		text("UPDATE some_table SET y=:y WHERE x=:x"),
		[{"x": 9, "y": 11}, {"x": 13, "y": 15}],
	)
	session.commit()

# 2025-07-09 15:31:50,975 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-09 15:31:50,975 INFO sqlalchemy.engine.Engine UPDATE some_table SET y=? WHERE x=?
# 2025-07-09 15:31:50,975 INFO sqlalchemy.engine.Engine [generated in 0.00007s] [(11, 9), (15, 13)]
# 2025-07-09 15:31:50,975 INFO sqlalchemy.engine.Engine COMMIT

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

# 2025-07-09 15:31:50,976 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-09 15:31:50,976 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("user_account")
# 2025-07-09 15:31:50,976 INFO sqlalchemy.engine.Engine [raw sql] ()
# 2025-07-09 15:31:50,976 INFO sqlalchemy.engine.Engine PRAGMA temp.table_info("user_account")
# 2025-07-09 15:31:50,976 INFO sqlalchemy.engine.Engine [raw sql] ()
# 2025-07-09 15:31:50,976 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("address")
# 2025-07-09 15:31:50,976 INFO sqlalchemy.engine.Engine [raw sql] ()
# 2025-07-09 15:31:50,976 INFO sqlalchemy.engine.Engine PRAGMA temp.table_info("address")
# 2025-07-09 15:31:50,976 INFO sqlalchemy.engine.Engine [raw sql] ()
# 2025-07-09 15:31:50,977 INFO sqlalchemy.engine.Engine 
# CREATE TABLE user_account (
# 	id INTEGER NOT NULL, 
# 	name VARCHAR(30), 
# 	fullname VARCHAR, 
# 	PRIMARY KEY (id)
# )
# 
# 
# 2025-07-09 15:31:50,977 INFO sqlalchemy.engine.Engine [no key 0.00006s] ()
# 2025-07-09 15:31:50,977 INFO sqlalchemy.engine.Engine 
# CREATE TABLE address (
# 	id INTEGER NOT NULL, 
# 	user_id INTEGER NOT NULL, 
# 	email_address VARCHAR NOT NULL, 
# 	PRIMARY KEY (id), 
# 	FOREIGN KEY(user_id) REFERENCES user_account (id)
# )
# 
# 
# 2025-07-09 15:31:50,977 INFO sqlalchemy.engine.Engine [no key 0.00005s] ()
# 2025-07-09 15:31:50,977 INFO sqlalchemy.engine.Engine COMMIT

```

The DDL create process above includes some SQLite-specific PRAGMA statements that test for the existence of each table before emitting a CREATE. The create process also takes care of emitting CREATE statements in the correct order. In more complicated dependency scenarios the FOREIGN KEY constraints may also be applied to tables after the fact using ALTER.

The `MetaData` object also features a `MetaData.drop_all()` method that will emit DROP statements in the reverse order as it would emit CREATE in order to drop schema elements. Overall, the CREATE / DROP feature of `MetaData` is useful for test suites, small and/or new applications, and applications that use short-lived databases. For management of an application database schema over the long term however, a schema management tool such as Alembic, which builds upon SQLAlchemy, is likely a better choice, as it can manage and orchestrate the process of incrementally altering a fixed database schema over time as the design of the application changes.

### Using ORM Declarative Forms to Define Table Metadata

When using the ORM, the process to declare `Table` metadata is usually combined with the process of declaring mapped classes. The mapped class is any Python class we’d like to create, which will then have attributes on it that will be linked to the columns in a database table. This style is known as declarative, and allows us to declare our user-defined classes and `Table` metadata at once.

#### Establishing a Declarative Base

When using the ORM, the `MetaData` collection is associated with an ORM-only construct commonly referred to as the **Declarative Base**. You can get a new Declarative Base by subclassing the SQLAlchemy `DeclarativeBase` class:

```py
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
	pass
```

Now when we make new subclasses of `Base`, each will be a new **ORM mapped class**, typically (but not exclusively) referring to a particular `Table` object.

The Declarative Base refers to a `MetaData` collection that is created for us automatically. As we create new mapped classes, they each will reference a `Table` within this `MetaData` collection:

```py
Base.metadata
# MetaData()
```
The Declarative Base also refers to a collection called `registry`, which is the central “mapper configuration” unit in the ORM. It's central to the mapper configuration process, allowing a set of ORM mapped classes to coordinate with each other. It's seldom accessed directly.

```py
Base.registry
# <sqlalchemy.orm.decl_api.registry object at 0x...>
```

#### Declaring Mapped Classes

With the `Base` class established, we can now define ORM mapped classes for the `user_account` and `address` tables in terms of new classes `User` and `Address`.

```py
from typing import List
from typing import Optional
from sqlalchemy import Mapped
from sqlalchemy import mapped_column
from sqlalchemy import relationship

class User(Base):
    __tablename__ = "user_account"

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(30))
	fullname: Mapped[Optional[str]]

	adresses: Mapped[List["Address"]] = relationship(back_populates="user")

	def __repr__(self) -> str:
	    return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"

class Address(Base):
	__tablename__ = "address"

	id: Mapped[int] = mapped_column(primary_key = True)
	email_address: Mapped[str]
	user_id = mapped_column(ForeignKey("user_account.id"))

	user: Mapped[User] = relationship(back_populates = "addresses")

	def __repr__(self) -> str:
		return f"Address(id={self.id!r}, email_address={self.email_address!r}"
```

`User` and `Address` are now called as ORM Mapped Classes, and are available for use in ORM persistence and query operations, which will be described later. Details about these classes include:

* Each class refers to a `Table` object that was generated as part of the declarative mapping process, which is named by assigning a string to the `DeclarativeBase.__tablename__` attribute. Once the class is created, this generated `Table` is available from the `DeclarativeBase.__table__` attribute.
* To indicate columns in the `Table`, we use the `mapped_column()` construct, in combination with typing annotations based on the `Mapped` type. This object will generate `Column` objects that are applied to the construction of the `Table`.
* For columns with simple datatypes and no other options, we can indicate a `Mapped` type annotation alone, using simple Python types like `int` and `str`.
* A column can be declared as “nullable” or “not null” based on the presence of the `Optional[<typ>]` type annotation (e.g. `User.fullname` above).
* Use of explicit typing annotations is completely optional. We could instead use more explicit type objects like `Integer` and `String` as well as `nullable=False` as needed within each `mapped_column()` construct.
* The `relationship()` construct is discussed more fully at Working with ORM Related Objects (below).
* The classes are automatically given an `__init__()` method if we don’t declare one of our own. The default form of this method accepts all attribute names as optional keyword arguments:
  ```py
  sandy = User(name="Sandy", fullname="Sandy Cheeks")
  ```
  It’s also an option to use an explicit `__init__()` method as well.
* The `__repr__()` methods are added so that we get a readable string output; there’s no requirement for these methods to be here.	

#### Emitting DDL to the database from an ORM mapping

Emitting DDL given the Declarative Base uses the same process as that described previously at Emitting DDL to the Database:

```py
Base.metadata.create_all(engine)

# 2025-07-10 11:53:43,172 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-10 11:53:43,172 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("user_account")
# 2025-07-10 11:53:43,172 INFO sqlalchemy.engine.Engine [raw sql] ()
# 2025-07-10 11:53:43,172 INFO sqlalchemy.engine.Engine PRAGMA temp.table_info("user_account")
# 2025-07-10 11:53:43,172 INFO sqlalchemy.engine.Engine [raw sql] ()
# 2025-07-10 11:53:43,172 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("address")
# 2025-07-10 11:53:43,172 INFO sqlalchemy.engine.Engine [raw sql] ()
# 2025-07-10 11:53:43,172 INFO sqlalchemy.engine.Engine PRAGMA temp.table_info("address")
# 2025-07-10 11:53:43,172 INFO sqlalchemy.engine.Engine [raw sql] ()
# 2025-07-10 11:53:43,173 INFO sqlalchemy.engine.Engine 
# CREATE TABLE user_account (
# 	id INTEGER NOT NULL, 
# 	name VARCHAR(30) NOT NULL, 
# 	fullname VARCHAR, 
# 	PRIMARY KEY (id)
# )
# 
# 
# 2025-07-10 11:53:43,173 INFO sqlalchemy.engine.Engine [no key 0.00004s] ()
# 2025-07-10 11:53:43,173 INFO sqlalchemy.engine.Engine 
# CREATE TABLE address (
# 	id INTEGER NOT NULL, 
# 	email_address VARCHAR NOT NULL, 
# 	user_id INTEGER, 
# 	PRIMARY KEY (id), 
# 	FOREIGN KEY(user_id) REFERENCES user_account (id)
# )
# 
# 
# 2025-07-10 11:53:43,173 INFO sqlalchemy.engine.Engine [no key 0.00004s] ()
# 2025-07-10 11:53:43,173 INFO sqlalchemy.engine.Engine COMMIT
```

## Working with Data

Components of this section:

* Using INSERT Statements: Core only (but useful to understand for ORM). For ORM-specific see below section Data Manipulation with the ORM.
* Using SELECT Statements: The `Select` construct emits SELECT statements for both Core and ORM centric applications and both use cases will be described here. Additional ORM use cases are also noted in the later section Using Relationships in Queries as well as the [ORM Querying Guide](https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html).
* Using UPDATE and DELETE Statements: Core-specific. For ORM-specific see the sections Updating ORM Objects using the Unit of Work pattern and Deleting ORM Objects using the Unit of Work pattern.

### Using INSERT Statements

This section details the Core means of generating an individual SQL INSERT statement in order to add new rows to a table. A SQL INSERT statement is generated directly using the `insert()` function. 

#### The insert() SQL Expression Construct

A simple example of `Insert` illustrating the target table and the VALUES clause at once:

```py
from sqlalchemy import insert
stmt = insert(user_table).values(name="spongebob", fullname="Spongebob Squarepants")
```

The above `stmt` variable is an instance of `Insert`. Most SQL expressions can be stringified in place as a means to see the general form of what’s being produced:

```py
print(stmt)

# INSERT INTO user_account (name, fullname) VALUES (:name, :fullname)
```

Our `Insert` construct is an example of a “parameterized” construct, illustrated previously in the Sending Parameters section.

#### Executing the Statement

```py
with engine.connect() as conn:
    result = conn.execute(stmt)
	conn.commit()

# 2025-07-10 13:06:41,533 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-10 13:06:41,533 INFO sqlalchemy.engine.Engine INSERT INTO user_account (name, fullname) VALUES (?, ?)
# 2025-07-10 13:06:41,533 INFO sqlalchemy.engine.Engine [generated in 0.00010s] ('spongebob', 'Spongebob Squarepants')
# 2025-07-10 13:06:41,533 INFO sqlalchemy.engine.Engine COMMIT
```

In its simple form above, the INSERT statement does not return any rows, and if only a single row is inserted, it will usually include the ability to return data generated during the INSERT of that row, most commonly an integer primary key value:

```py
result.inserted_primary_key

# (1, )
```

#### INSERT usually generates the “values” clause automatically

If we don’t actually use `Insert.values()` and just print out an “empty” statement, we get an INSERT for every column in the table:

```py
print(insert(user_table))

# INSERT INTO user_account (id, name, fullname) VALUES (:id, :name, :fullname)
```

If we take an `Insert` construct that has not had `Insert.values()` called upon it and execute it rather than print it, the statement will be compiled to a string based on the parameters that we passed to the `Connection.execute()` method, and only include columns relevant to the parameters that were passed.

```py
with engine.connect() as conn:
    result = conn.execute(
	    insert(user_table),
		[
		    {"name": "sandy", "fullname": "Sandy Cheeks"},
			{"name": "patrick", "fullname": "Patrick Star"},
		],
	)
	conn.commit()

# 2025-07-10 15:44:06,874 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2025-07-10 15:44:06,874 INFO sqlalchemy.engine.Engine INSERT INTO user_account (name, fullname) VALUES (?, ?)
# 2025-07-10 15:44:06,874 INFO sqlalchemy.engine.Engine [generated in 0.00009s] [('sandy', 'Sandy Cheeks'), ('patrick', 'Patrick Star')]
# 2025-07-10 15:44:06,874 INFO sqlalchemy.engine.Engine COMMIT
