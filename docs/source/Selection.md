
# Selection


## Why "Selection" ?

In CRUD you can do some selelection with filters. See {ref}`selections <selection_route>` for that.
But you can do more, with _pre-defined selections_ related to the business, like :

* All books borrowed with the return date in less than one week
* All users with roles "ADMIN"
* ...

All thoses selections can be done by the client with the appropriate filter. But using Selections, you can do that on the backoffice side, and propose to clients 
named selections. 

etc...


## Definition 

A selection is a *named* list of Items with sub elements provided by a [path](https://stricto.readthedocs.io/en/latest/readme.html#selectors).

An selection is compose by :
1. a list of [selectors](https://stricto.readthedocs.io/en/latest/readme.html#selectors)
2. a [filter](https://stricto.readthedocs.io/en/latest/readme.html#matching) or a function which return a selector
3. a sort (optional) which is a list or [selectors](https://stricto.readthedocs.io/en/latest/readme.html#selectors)
4. Some rights



```{important}
A selection must be registered to a {py:class}`Collection() <backo.Collection>` (with {py:meth}`.register_selection() <backo.Collection.register_selection>` call)
```

```{tip}

* If the list of selectors is None, all the Item will be returned.
* `_id` are prepend to the list of selectors. You don't need to add them.

```


## example

This is a selection of borrowed books (all collections ar not described).


`````{tab-set}
````{tab-item} simple

```python
# list of borrowed books
borrowed_book_select = Selection( [ "$.title", "$.borrow.user.login" ], 
    filter=SFilter( '$.borrowed', Operator.EQ, True ), # or filter=function()
    sort=[ "-$.borrow.date", "$.title" ] 
    )
books.register_selection("borrowed_books", borrowed_book_select)
```

````
````{tab-item} with function

```python

def must_return_today():
    return SFilter( "$.borrow.return_date", Operator.GT, datetime.now() )

# list of borrowed books
comeback_today_select = Selection( [ "$.title", "$.borrow.user.login" ], 
    filter = must_return_today
    sort = [ "-$.borrow.date", "$.title" ] 
    )
books.register_selection("comeback_today", comeback_today_select)
```

````
````{tab-item} with rights

```python

def can_execute_borrowed_books(right_name: str, book: Item) -> bool:
    """Tel if current_user can do this selection
    """
    if current_user.has_role("EMPLOYEE"):
        return True
    return False

# list of borrowed books
borrowed_book_select = Selection( [ "$.title", "$.borrow.user.login" ], 
    filter=SFilter( '$.borrowed', Operator.EQ, True ), # or filter=function()
    sort=[ "-$.borrow.date", "$.title" ]
    can_read = can_execute_borrowed_books
    )
books.register_selection("borrowed_books", borrowed_book_select)
```

````

`````



### rights for selections

A right is a function (or a lambda) with these parameters, and must return a boolean.

```python
def your_function_name(right_name: str, o: Item) -> bool:

```

| right    | description                                                 |
| -------- | ----------------------------------------------------------- |
| can_read | Check if [current_user](#current_user) can do the selection |



### routes


See {ref}`Selection routes <named_selection_route>` for the resulting RESTfull API routes.


And to call the selection...

Some example :

```bash
curl -X GET 'http://localhost/media_library/coll/books/_selections/borrowed' 
  '{"result": [
     ["666", "Docker as BDSM toy", "Rambo"], 
     ["1234", "Yml is not a language", "Rambo"]
    ],
    "_skip": 0, "_page": 10}'
curl -X GET 'http://localhost/media_library/coll/books/_selections/borrowed?title.$reg=Docker'
    '{"result": [
       ["666", "Docker as BDSM toy", "Rambo"]
     ],
     "_skip": 0, "_page": 10}'   

curl -X GET 'http://localhost/media_library/coll/books/_selections/borrowed?_total=1' 
   '{ "total" : 2 }'
# or
curl -X GET 'http://localhost/media_library/coll/books/_selections_total/borrowed' 
   '{ "total" : 2 }'
```



## API Reference

See {py:class}`Selection() <backo.Selection>` 