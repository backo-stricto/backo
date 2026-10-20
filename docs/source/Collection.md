# Collection

The {py:class}`Collection() <backo.Collection>` object is the link between {doc}`Item` and {doc}`Databases <Database>`.


A collection is attached to a ```backoffice``` and is composed by :

1. An {doc}`Item`. It describe the _structure_ of the object in the collection
2. A {doc}`Database handler <Database>`, to say where to get/store/select items.
3. Some {doc}`rights <Authentication>`
3. Some {doc}`Action <Action>`
3. Some {doc}`Selection <Selection>`


## Usage


```python
from backo import Collection, Backoffice

books = Collection(
    "books",
    books_item,
    connector,
    can_create=can_create,
    can_modify=can_modify,
    can_delete=can_delete,
)

# Add an action
books.register_action("borrow", borrow_action)
# Add a Selection
books.register_selection("borrowed", borrowed_book_select)

myapp = Backoffice("media_library")
myapp.register_collection(books)

```

## API Reference

See {py:class}`Collection() <backo.Collection>` 