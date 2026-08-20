"""
Attribut transformer
"""

class Transformer():
    """
    Transform attributes

    used to rewrite the path for filtering, projection...

    """
    def __init__(self, key_path : list [str ], backo_type:str = None ):
        self.key_path = key_path
        self.backo_type = backo_type

    def on_load(self, _loaded_object:dict, _key_path : list [str ]) :
        return
        
    def on_create(self, _obj:dict, _key_path : list [str ]):
        return
    
    def on_save(self, _obj:dict, _key_path : list [str ]):
        return

    def get_key_path( self ):
        return self.key_path

    def must_be_store_in_db( self ):
        return True

