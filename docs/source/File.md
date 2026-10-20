# Files


backo can manage files in a simple way : Like other {ref}`types <item_types>`.
You can use File() or BlobFile().

| object     | Description                                                                                                                  |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------- |
| File()     | Generic object to manage a file. You need to define a FileConnector to indicate the object File where to store the file      |
| BlobFile() | File data is integrated literally into the datastructure, so there is no need for a FileConnector. Reserved for small files. |

You can use all {ref}`options <item_options>` for Files like other fields. 


However there are extra specific parameters :

| Option                                | Default | Description                                                                                                                  |
| ------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------- |
| ```mime_types=[ str ]```              | None    | The list of allowed content types                                                                                            |
| ```max_size=8192```                   | None    | The maximum size of the file                                                                                                 |
| ```work_connector=FileConnector```    | None    | File working copy connector (main file location)                                                                             |
| ```storage_connector=FileConnector``` | None    | Second fileConnector used to store the file permanently after processing. If unset, file unique location is *work_connector* |


Attributes and methods of the File object:

```python
a = BlobFile()

a.set(b'Hello word')
# or
a.set_content(b'Hello word')

a.filename = "my_hello.txt"
a.content_type # -> 'text/plain'
a.size # -> 9
a.file_id # -> A random id

# Get the content of the file
a.get_content() # -> b'Hello word'

```


## BlobFile()


Add a file with inlined data: 

```python
an_author = Item({
    'name' : String( require=True ),
    'surname' : String(),
    'pict' : BlobFile( require=True , mime_types=[ 'image/jpeg', 'image/png' ])
    'books' : RefsList( coll='books', field="$.author" )
})
```
## File()


Add a file stored in a specific location on the file system:

```python
an_author = Item({
    'name' : String( require=True ),
    'surname' : String(),
    'pict' : File( require=True , mime_types=[ 'image/jpeg', 'image/png' ], work=FileSystemConnector( path="/path/to/store/the/file" ) )
    'books' : RefsList( coll='books', field="$.author" )
})
```



## routes

In a general context, {doc}`Routes are RESTful JSON API calls <Routing>`. But with files, every routes (CRUD, actions, ... )
can be called in two ways :

1. With files embedded in JSON in string format (for text files) or with base64 encoded (for other).
    
    ```bash
        # creating an author with a pict
        curl -X POST 'http://localhost/myApp/authors/' -d '{"surname":"John","name":"Rambo", "pict" : "base64:Sm9obiBwaWN0"}'
    ```
   
2. With a multipart route
    
    Each file is a part of the HTML multipart message. The JSON structure must be encoded in a ```_json``` multipart part.
   
    ```bash
        # creating an author with a pict
        curl -X POST -F _json='{"surname":"John","name":"Rambo"}' -F pict=@rambo.png http://localhost/myApp/authors/

        # Modifying the author picture
        curl -X PUT -F pict=@rambo1.png http://localhost/myApp/authors/id_of_rambo

        # Modifying the author picture and name
        curl -X PUT  -F _json='{ "name":"Rimbaud" }' -F pict=@rimbaud.png http://localhost/myApp/authors/id_of_rambo

    ```


3. link to the file are GET \<my-app-name\>/\<collection name\>/\<_id\>/\<path\>



## API Reference

See {py:class}`File() <backo.File>` 