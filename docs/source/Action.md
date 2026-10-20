
# Action


## Why "Action" ?

With CRUD, the client can modify the database in one **or more** restfull API call. If the modification is complex, it'll need probably more than one update / creation.
For example, imagine the following business modification :

"A user want to borrow a book, but you must verify first that he haven't already borrow to much books (In this library a user can only borrow 3 book at once). And when the book is borrowed, send him a notification by email"

What will be done exactly :

1. The client, get the user (and its _id). 
2. The client must verify the ability to borrow a book by doing a select to the book collection to see if a less than 3 books are actually borrowed by this user _id.
3. Update the book _id with the user _id (and probably some dates) (a http `PUT`)
   
   At this point, **the server should do the same verification** (the user _id is not already)

4. The server must send the notification (how ?)


With {py:class}`Action() <backo.Action>`,  you will define a dedicated endpoint in the restfull API route, with a dedicated function behind. in this function, you can do what you want (verification, modifications, notifications... whatever). The client just have to call the the point with good parameters. 


## Definition 

An {py:class}`Action() <backo.Action>` is a way to do some complex modifications to an Item or more. More than just a PATCH/PUT (modification). It can modify more than one item, and more than one collection, 


An action is compose by :
1. an [Stricto Dict](https://github.com/backo-stricto/stricto?tab=readme-ov-file#dict) for parameters
2. a function (**The** function to call to do the job)
3. Some rights (if the action make sens (`exists=`) and if current_user has right to call it (`can_execute=`)) 


```{important}
An action must be registered to a {py:class}`Collection() <backo.Collection>` (with {py:meth}`.register_action() <backo.Collection.register_action>` call)
```

An example is a better than any explanations ... See below

## example

This is an action to *borrow a book*, with a start time at daytime.
(all collections are not described)

`````{tab-set}
````{tab-item} definition

```python

def borrow(action: Action, book: Item, **kwargs) -> None:
    """borrow the book"""
    book.borrow.user = action.user_id
    book.borrow.date = datetime.now().replace(microsecond=0)
    book.borrow.return_date = action.return_date
    book.save(**kwargs)

#
# Definition of the action
borrow_action = Action(
    {
        "user_id": String(require=True), 
        "return_date": Datetime(require=True)
    },
    borrow,
    can_execute=can_borrow,
    exists=can_see_borrow_action,
)

# Add the action to the book collection
books.register_action("borrow", borrow_action)

```

````
````{tab-item} rights
```python
def can_borrow(right_name: str, book: Item) -> bool:
    """Tel if current_user can execute the borrow action
    """
    if current_user.has_role("EMPLOYEE"):
        return True
    return False


def can_see_borrow_action(right_name: str, book: Item) -> bool:
    """Tel the borrow action is a nonsense ?
    """
    return not book.borrowed
```
````
`````
### rights

A right is a function (or a lambda) with these parameters, and must return a boolean.

```python
def your_function_name(right_name: str, o: Item) -> bool:

```

| right       | description                                                   |
| ----------- | ------------------------------------------------------------- |
| can_execute | Check if [current_user](#current_user) can execute the action |
| can_see     | exists                                                        | 


### routes


See {ref}`Actions routes <action_route>` for the resulting RESTfull API routes.



## API Reference

See {py:class}`Action() <backo.Action>` 