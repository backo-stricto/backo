# Item

The Item is the main object of backo. It describe the object of a {doc}`Collection`, its fields, constraints and more of each fields.

Item is based on a [stricto](https://stricto.readthedocs.io/en/latest/) Dict.

Like pydantic or other description and validation tools, you will describe your object (the Item) using Stricto. It is simple :

## Example

as you can see, the description of a Item is _self meaning_. All options are optional parameters.

```python
user = Item(
    {
        "login": String(require=True, can_modify=can_modify_login, default=""),
        "email": String(),
        "roles": List(
            String(union=["ADMIN", "EMPLOYEE", "USER"], default="USER"),
            can_modify=can_modify_roles,
        ),
        "rent": Dict({"books": RefsList(coll="books", field="$.borrow.user")}),
    }
)
```

(item_types)=
## Types

All Python basic classes are implemented in ```stricto/backo```. The same with uppercase.

| backo | python type |
| - | - |
| Bool() | bool | 
| Int() | int | 
| Float() | float | 
| String() | string | 
| List() | list | 
| Dict() | dict | 
| Tuple() | tuple | 
| Bytes() | bytes | 
| Datetime() | datetime | 
| Extend() | The extension abstract class for building your own type | 

and some other specific fields :

| backo | signification |
| - | - |
| Ref() | {ref}`a Reference One to Many <Ref>` |
| RefsList() | {ref}`a Reference Many to Many or to One <RefsList>` |
| File() | {doc}`a file <File>` |
| BlobFile() | {doc}`a file in memory <File>` |


(item_options)=
## Options

| Option | Default | Description |
| - | - | - |
| ```required=True\|False``` | False | Check whether the field must have a value. |
| ```description="whatever you want"``` | None | Set a description for the item |
| ```default=666\|func``` | None | set a default value |
| ```in\|enum\|union=[ 1, 2, 3, 5 ]\|func``` | None | Value must be in the list or pass the function check. |
| ```transform=func``` | None | Set a function that [transforms](#transform) the value before assignment. |
| ```constraint=func``` | None | Set a function to {ref}`constraint` the value before asssignment. |
| ```constraints=[func]``` | None | Same as above but for a list of {ref}`constraint` |
| ```set=func``` | None | For read-only items ; set a function that will compute the value from others attributes. See {ref}`computation` |
| ```exists=func``` | True | Set a function to check whether the object exists based on values from other attributes. See  {ref}`exists` for details |
| ```can_read=func``` | True | Set a function to check whether the object is readable. see {doc}`Authentication` for details |
| ```can_modify=func``` | True | Set a function to check whether the object is changeable (read-only value). see  {doc}`Authentication` for details |
| ```on=(event_name, function)``` | None | Register a function to be trigged when the specified event occurs. see {ref}`events` for details |
| ```views=[ "view1", "!view2" ]``` | [] | Define the views this attribute is included or excluded from.. see {ref}`views` for details |
| ```meta_data_handler=GenericMetaDataHandler``` | StandardMetaDataHandler() | Define the {ref}`Metadata handler <metadata>` for this item |

(constraint)=
### Constraint 


```python
# example
from backo import Item, Int


def check_pair(_o, value, _old_value): 
    """
    return true if pair

    o: the root object
    value: the value of this object
    _old_value : the previous value
    """
    return not value % 2

a=Item({
    "b" : Int( default = 0, constraint=check_pair ),        # check before setting
    "d" : Int( constraint=lambda value, o : not value % 2 ), # same as above, with a lambda
    "c" : Int( constraints=[ check_pair ] ),                # A list of constraints
})

a.b = 2 # OK
a.c = 3 # -> raise an error
```


(exists)=
### Exists 

This is a kind of _conditional field_, depending on the value of another field.

example :

```python
# example
from backo import Dict, Int, String

def check_if_female(value, o):
    """
    return true if Female
    """
    if o.gender == "Male":
        return False
    return True

cat=Dict({
    "name" : String(),
    "gender" : String( default = 'Male', in=[ 'Male', 'Female' ]),
    "female_infos" : Dict(
        {
        "number_of_litter" : Int(default=0, required=True)
        # ... some other attributes

    }, exists=check_if_female )
})

cat.set({ "name" : "Felix", "gender" : "Male" }
cat.female_infos   # -> None
cat.female_infos.number_of_litter = 2 # -> Raise an Error, This field doesnt exists

cat.gender = "Female"
cat.female_infos.number_of_litter = 2 # -> Ok
cat.female_infos # -> { "number_of_litter" : 2 }
```

#### Events

See {ref}`On <events>`

(events)=
### On 

Each Item has a specific workflow and triggers specific events. The following events are triggered when the functions above are called:

| function  | event before    | event after |
| --------- | --------------- | ----------- |
| .load()   |                 | "loaded"    |
| .save()   | "before_save"   | "saved"     |
| .delete() | "before_delete" |             |
| .create() | None            | "created"   |

#### Example
Below is a simple use case on how to use these events:

```python
        def rip( event_name, root, me, **kwargs ):
            """
            event_name = "before_delete"
            root = cat Item
            me = cat Item too
            """
            # Do what you want

        cat = Item( {
                'name' : String()
                'birth' : Datetime()
            }
            on=[ ( "before_delete", rip ) ]
        )
```




(computation)=
### Set 

Set is the way to make "computation" in backo. The value is the result of a function.


```python
def set_borrowed(book: Item) -> bool:
    """compute if the book is currently borrowed

    :param book: the current book
    :type book: Item
    :return: borrowed or not
    :rtype: bool
    """
    if book.borrow is None:
        return False
    if book.borrow.return_date is None:
        return False
    if book.borrow.return_date > datetime.now():
        return True
    return False

books_item = Item(
    {
        "title": String(require=True, default=""),
        "borrowed": Bool(set=set_borrowed),
        "borrow": Dict(
            {
                "user": Ref(
                    coll="users",
                    field="$.rent.books",
                ),
                "return_date": Datetime(require=True),
                "date": Datetime(require=True),
            },
        ),
    }
)


```

```{tip}
The recomputation is done every changement into the Item. 
You don't have to trigg the computation by yourself.
```

```{tip}
By default a set= field is not saved into the DB. It is recomputed on the load(). 
if you want to save it (and no recomputation), add ``view=[ "save" ]``
```

```{caution}
Avoid doing some selections into the set= function. You can fall into infinite loop.
```



(transform)=
### Transform 

Do some transformation on the value before set.

```python
# example
from backo import Item, String

def upper(_o, value, _old_value):
    """
    transform the value into upper

    _o     : the full object
    value : the current value given ("worldcompagny" in this example).
    _old_value : the previous value 
    """
    return value.upper()

user=Item({
    "name" : String( transform=upper ),
})

user.name="rambo"
print(user.name) # -> "RAMBO"
```



(views)=
### Views 


Soon

(meta)=
## Meta data


### _id

You dont't have to care about *_ids* in your item description. Backo will alter schema to add `_id` for each Item.

(metadata)=
### metadata handler


A {py:class}`Metadata handler <backo.GenericMetaDataHandler>` is an alteration of the Item to add some fields.
The purpose is to store direcly in the ITam, in the DB some informations like the creation date, modification date, who has modified the object, or whatever you want.


There is two MetadataHandler out of the box :

| meta data handler | Description |
| -- | -- |
| {py:class}`Empty metadata handler <backo.GenericMetaDataHandler>` | A metadata... with nothing ! |
| {ref}`Standard metadata handler <StandardMetaDataHandler>` | A metadata... with create time, ctime, attache to ```_meta``` field |

(StandardMetaDataHandler)=
#### StandardMetaDataHandler

The provided *StandardMetaDataHandler* give this following Dict() :

```python
Dict(
    {
        "ctime": Datetime(description="Creation time"),
        "mtime": Datetime(description="Last modification time"),
        "created_by": Dict(
            {"_id": String(), "login": String(default="ANONYMOUS")},
            description="Created by",
        ),
        "modified_by": Dict(
            {"_id": String(), "login": String(default="ANONYMOUS")},
            description="Modified by",
        ),
    },
    can_modify=False,
    description="Meta data information",
)
```

```{tip}
You can notice that everything is _read only_. Meta datas are modified by the server
```

## API Reference

See {py:class}`GenericMetaDataHandler() <backo.GenericMetaDataHandler>`