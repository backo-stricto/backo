
# Quickstart


## Installation

```bash

# basic
pip install backo

# With mongo
pip install backo[mongo]

# With postgres
pip install backo[postgres]

```

## backo_init

If you prefere, on your terminal, launch `backo_init` and answer to questions.

```bash
$ backo_init

Backo>
────────────────────────────────────────
Welcome to backo  
First you must chose a name for your application.
Lets go.
────────────────────────────────────────
? Name of the application 

...

```

## Step 1 - Backoffice


First, you must create your `Backoffice()`. This is the main object.

The Backoffice object manage :

* The Collection (aka table) {ref}`see Step 2 - Collection <step-2-collection>` 
* Api routing with flask
* {py:class}`current_user() <backo.current_user>` for authentication


`````{tab-set}
````{tab-item} Sample call
```python
from backo import Backoffice

my_backoffice = Backoffice("media_library")
```
````

````{tab-item} with option(s)
```python
from backo import Backoffice

my_backoffice = Backoffice("media_library", "1.0.0")
# The version will be in the restfull route path
```
````

`````


Here is an example.

```python
from flask import Flask
from backo import Backoffice

# -- Define your backoffice
my_backoffice = Backoffice("myApp")

# Register your collections
my_backoffice.register_collection(books)
my_backoffice.register_collection(users)
# ... and so on

# Your flask application
flask = Flask(__name__)

# -- Buid routes for this application
my_backoffice.build_routes(flask)

# Start the flask server
flask.run(host="0.0.0.0", port=80)
```

```{tip}
At this point, flask export API restfull routes, and more. See {doc}`Routing` for details on routes provided.
```


For full documentation see {py:class}`Backoffice api reference <backo.Backoffice>`


(step-2-collection)=
## Step 2 - Collection

Next, you must create a {doc}`Collection() <Collection>` objectf for each _table_ (if you think like SQL database), or _collection_ (in a mongodB meaning). The table is the description of an object in your application.

The Collection object manage :

* The descrition of sthe component object wich is called {doc}`Item() <Item>`
* where to store datas. See {doc}`Database management <Database>`
* optional some {doc}`Action() <Action>`
* optional some {doc}`Selection() <Selection>`

In our previous example, whe see two collections : `books` and `users`.


`````{tab-set}
````{tab-item} Sample call
```python
from backo import Collection

users = Collection("users", item, db_connector)
```
````

`````
Here is an example :

```python
# Define a collection 
users = Collection( 
    "users",
    Item({
        "name": String(),
        "surname": String(),
        "male": Bool(default=True),
    }),
    db_connector_for_users,
)
my_backoffice.register_collection(users)

```

For full documentation see {py:class}`Collection() api reference <backo.Collection>`




(step-3-item)=
## Step 3 - Item

Next, you must create a {py:class}`Item() <backo.Item>` objectf to describe what the object look like.
It is probably the more complexe object because it manage a lot of stuffs :

* Each field of the object (which will be transformed in a collum in a SQL Table), with its type (string, int, float, bool...)
* It's _classical_ constraints like the default value, if it is required...
* references to other `Collections` (for cardinalities)
* some rights on fields (who can read ? who can modify ? )

For full documentation see {py:class}`Item() api reference <backo.Item>`

```{seealso}
backo is based on [stricto](https://stricto.readthedocs.io/en/latest/) for Item definition and fields.

Please have a look at the [stricto documentation](https://stricto.readthedocs.io/en/latest/)
```


```{tip}

It is _normal_ to see some uppercase types ("String" instead of "string" or "str" ). It is [stricto](https://stricto.readthedocs.io/en/latest/)

```


`````{tab-set}
````{tab-item} Sample call
```python
from backo import Item

user = Item({
        "name": String(),
        "surname": String(),
        "male": Bool(default=True),
    }),

users = Collection( "users", user, db_connector_for_users)
```
````
````{tab-item} with ref
```python
from backo import Item

user = Item({
        "name": String(),
        "surname": String(),
        "addr": Ref(coll="addrs", field="$.users", required=True),
        "male": Bool(default=True),
    }),

users = Collection( "users", user, db_connector_for_users)

```
````
````{tab-item} with right
```python
from backo import Item

def who_can_modify(right_name: str, user: Item) -> bool:
    """Check if can modify the name of the user """

    # Do here what you want
    if current_user.has_role(["ADMIN", "EMPLOYEE"]):
        return True
    return False

user = Item({
        "name": String( can_modify = who_can_modify ),
        "surname": String(),
        "addr": Ref(coll="addrs", field="$.users", required=True),
        "male": Bool(default=True),
    }),

users = Collection( "users", user, db_connector_for_users)

```
````

`````

## Coding

After the `my_backoffice.build_routes(flask)` and the server started (`flask.run(host="0.0.0.0", port=5000)`), route API are set. You can access, CRUD objects in all collections. But you can programmatically do everything, access all Items, create, update, save, select, etc...

For example (based on previous ex):



`````{tab-set}
````{tab-item} create
```python
from backo import Item, Collection, Backoffice

# get the collection from the backoffice
users = my_backoffice.users

# Create a user in the Database
johnny = users.create({ "name" : "Rambo", "surname" : "John" })
print(f"user {johnny._id} created")

```
````
````{tab-item} update
```python
from backo import Item, Collection, Backoffice, SFilter, Operator

# get the collection from the backoffice
users = my_backoffice.users
_id = "1234"
johnny = users.get_by_id( _id ) # Or raise an Error if Not found
# or 
johnny = users.select_one( SFilter("$.name", Operator.EQ, "Rambo" ) ) # Or raise an Error if Not found

print(f"user {johnny.name} from from the DB")
user.surname = 12 # -> Raise a TypeError
# make some change
user.male = False
# save into the DB
user.save()

```
````
````{tab-item} delete
```python
from backo import Item, Collection, Backoffice, SFilter, Operator

# get the collection from the backoffice
users = my_backoffice.users
_id = "1234"
johnny = users.get_by_id( _id ) # Or raise an Error if Not found
# or 
johnny = users.select_one( SFilter("$.name", Operator.EQ, "Rambo" ) ) # Or raise an Error if Not found

print(f"user {johnny.name} from from the DB")
# dropped from the DB
user.delete()

```
````

`````

See {doc}`Coding` for details about programing backo

