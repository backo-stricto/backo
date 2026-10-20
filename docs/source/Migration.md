
# Migration



If you change an {doc}`Item` of a {doc}`Collection`, data currently stored in the database can be rejected by the model.
You need to migrate them and there is a tool for that.

## How it works

You have to write a script importing your backoffice object call the ```.migrate()``` method of the backoffice, and provide a function to make change to the object.

Below a migration function example:

```python
def transform_function( o: dict) -> dict:
    """ Do what you want and return o"""
    # Adding a new key
    if 'new_key' not in o:
        o['new_key'] = ...
    # removing
    del o['unwanted_key']
    # ...
    return o
```

```{attention}
Note that object are ```dict``` and not ```Item```. Migration give a row access to {doc}`DB Handlers <Database>` and dont care about Item, rights, Refs, etc...
```


By default, the strategy for migration is ```MigrationStrategy.DRY_RUN```. So you will broke nothing. ```MigrationStrategy.DRY_RUN``` will do all work except saving the object in the DB.

```{caution}
There is no check of *rights* and *current_user* during migration. metadatas (see {ref}`metadata`) are not updated.
```


## example

Imagine a *books* collection. 
You modify the book {doc}`Item` to add a *note* field which is a float and is required. 
If you do nothing, the {py:meth}`.load() <backo.Item.load>` of a old item in the DB will failed on the new field *note* because this new field is required. 
Here is an example for migrating data:


`````{tab-set}
````{tab-item} check
```python
from backo import MigrationStrategy

# ---------------------------------------------
# Check if a data match the model
# it raise an error at first _id 
# ---------------------------------------------
report = myapp.migrate("books", _id="my_book_id") # check a specific _Id
# or
report = myapp.migrate("books", _ids=["my_book_id1", "my_book_id2"]) # check a list of _Id
# or
report = myapp.migrate("books")  # check all ids

```

````
````{tab-item} definition

```python
# --------------------------------------------
# Do a changement
# example you must now have a note field with a float value
# --------------------------------------------
def update_with_note(o: dict) -> dict:
    """
    this the function for doing operation on objects before setting them into the Item
    You can do what you want.
    """
    if "note" not in o:
        o["note"] = 10.0
    return o
```
````

````{tab-item} migrate
```python
from backo import MigrationStrategy

# Check if OK (dry_run is True by default)
report = mybackoffice.migrate("books", update_with_note, _id="my_book_id")
# or
report = mybackoffice.migrate("books", update_with_note, _ids=["my_book_id1", "my_book_id2"])
# or
report = mybackoffice.migrate("books", update_with_note)  # All ids

# do it for real
report = mybackoffice.migrate("books", update_with_note, _id="my_book_id", dry_run=False)
# or
report = mybackoffice.migrate(
    "books", update_with_note, _ids=["my_book_id1", "my_book_id2"], strategy=MigrationStrategy.EXECUTE
)
# or
report = mybackoffice.migrate("books", update_with_note, strategy=MigrationStrategy.EXECUTE)  # All ids

```
````


`````

## MigrationStrategy options

| option | description |
| - | - |
| ```MigrationStrategy.DRY_RUN``` | Don't change anything, just display and report diffs | 
| ```MigrationStrategy.EXECUTE``` | Do changements and save in DB if needed. report diffs | 
| ```MigrationStrategy.FORCE``` | Do changements and rewrite data in DB. report diffs | 




## Report

The migration returns a report structure :

* ```report.nochanges._ids``` 
  The list (array) of unchanged _ids
* ```report.total```
  The number of unchanged _id durion this migration
* ```report.changes._ids```
  The list (array)  of _ids which are changed during this migration
* ```report.changes.total```
  the number of changed _ids.
* ```report.changes.diff```
  The list (array) of diff for each _id. The format is [DeepDiff](https://pypi.org/project/deepdiff/)



