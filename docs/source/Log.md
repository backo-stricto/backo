
# Logs and debug

The log system is based on [logging Python module](https://docs.python.org/3/library/logging.html)

You must first design your logging system with handlers. Then you can write the logs outputs.

## step 1 : Select or Create a specific log system

To select create a specific log system :

```python
from backo import log_system, LogLevel

# create your own sub logger
log = log_system.get_or_create_logger("custom")

# write messages
log.info("hey this is my first debug message")
log.debug("and it works")
```
## step 2 : Set the level

To select create a specific log system :

```python
from backo import log_system, LogLevel

# Set the level for all
log_system.setLevel( LogLevel.INFO )

# create your own sub logger with its specific logging level
log = log_system.get_or_create_logger("custom")
log.setLevel( LogLevel.DEBUG )

log.debug("and it works")
```

## step 3 : Define the output

You must define the output (where to send logs)

```python
from backo import log_system, LogLevel
# To write all file to stderr
log_system.add_handler( log_system.set_streamhandler() )

# To write in a file
log_system.add_handler( log_system.set_filehandler("/var/log/mylog.log") )

# write my own log into a specific file
log = log_system.get_or_create_logger("custom")
log.add_handler( log_system.set_filehandler("/var/log/custom.log") )

```

## Check log 

To debug log (where i send which log). Ther is a command for that :

```python

# To see
log_system.infos()
# print some available informations about log system (levels, handlers)
```

## stack()

If you need, you can had the ```stack()``` into your message, to get a nice stack call:

```python
log = log_system.get_or_create_logger("custom")
log.setLevel(logging.DEBUG)

# somewhere in you code
log.debug(f'this is a debug message with stack {stack()}')
# ...
```

Will output something like :


```bash
DEBUG-custom- "/my_path/myfile.py", line 196 : this is a debug message with stack
  / 
  \ called by "/my_path/myfile.py", line 128, in sub_test_set_get_sample
   \ called by "/my_pathtests/test_file.py", line 140, in test_set_get_sample
    \ called by "/usr/lib/python3.12/unittest/case.py", line 589, in _callTestMethod
     \ called by "/usr/lib/python3.12/unittest/case.py", line 634, in run
      \ called by "/usr/lib/python3.12/unittest/case.py", line 690, in __call__
       \ called by "/usr/lib/python3.12/unittest/suite.py", line 122, in run
        \ called by "/usr/lib/python3.12/unittest/suite.py", line 84, in __call__
         \ called by "/usr/lib/python3.12/unittest/suite.py", line 122, in run
          \__
```


## current loggers

Currently available loggers are :

| logger      | description                            |
| ----------- | -------------------------------------- |
| backoffice  | The main Backoffice system             |
| Item        | The database itself (CRUD operations ) |
| ref         | Ref and RefsList objects               |
| transaction | transactions and roolback              |
| yml         | yaml database connector                |
| mongo       | mongo database connector               |
| select      | selections                             |
| migration   | see {doc}`Migration`            |

