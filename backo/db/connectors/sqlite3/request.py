# pylint: disable=relative-beyond-top-level, too-few-public-methods
"""
Attribut mapper for mongo db connector
"""

from typing import Any
from .attribute_mapper import Sqlite3AttributeMapper
from .item_mapper import Sqlite3ItemMapper
from ...request import (
    DeleteRequest,
    UpdateRequest,
    CreateRequest,
    SearchRequest,
    SelectRequest,
)


class Sqlite3SelectRequest(SelectRequest):
    pass

class Sqlite3SearchRequest(SearchRequest):
    pass

class Sqlite3UpdateRequest(UpdateRequest):
    pass

class Sqlite3DeleteRequest(DeleteRequest):
    pass

class Sqlite3CreateRequest(CreateRequest):

    requests : dict[ str, dict [ str, Any ] ] = {}

    def __init__(self, data, item_mapper : Sqlite3ItemMapper ):
        self.item_mapper = item_mapper
        super().__init__(data)

    def flatten( self, table_name: str, data:Any, backo_path: list [ str ], db_path: list [ str ]):

        if isinstance( data, dict ):
            for key, value in data.items():
                backo_p = backo_path.copy()
                backo_p.append( key )
                attribute_mapper:Sqlite3AttributeMapper = self.self.item_mapper.get_mapper( f'$.{ '.'.join(backo_p) }' )

                db_p = db_path.copy()
                db_p.append( attribute_mapper.get_for_projection() )

                self.flatten( table_name, value, backo_p, db_p )

            return
        
        # A list
        if isinstance( data, list ):
            sub_table_name = attribute_mapper.get_sub_table_name( table_name, '_'.join( db_p ))
            self.flatten( sub_table_name, data, backo_p, db_p )
            return

        # A value
        self.requests[table_name][ '_'.join( db_p )] = data
    

    def split( self, table_name:str, item_mapper: Sqlite3ItemMapper )-> None:
        self.requests[table_name] = {}

        self.flatten( table_name, self._data, [], [] )





