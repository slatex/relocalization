"""
Catalog of definitions
"""
from flexi.gf.mast import MAst


class Catalog:
    def __init__(self):
        # maps symbol URIs to
        self.definitions: dict[str, list[list[MAst]]] = {}



