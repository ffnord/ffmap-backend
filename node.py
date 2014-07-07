from collections import defaultdict

class NoneDict:
    """Act like None but return a NoneDict for every item request.

    This is similar to the behaviour of collections.defaultdict in that
    even previously inexistent keys can be accessed, but nothing is
    stored permanently in this class.
    """
    __repr__ = lambda self: 'NoneDict()'
    __bool__ = lambda self: False
    __getitem__ = lambda self, k: NoneDict()
    __json__ = lambda self: None
    __float__ = lambda self: float('NaN')
    def __setitem__(self, key, value):
        raise RuntimeError("NoneDict is readonly")

class Node(defaultdict):
    _id = None
    def __init__(self, id_=None):
        self._id = id_
        super().__init__(NoneDict)

    def __repr__(self):
        return "Node(%s)" % self.id

    @property
    def id(self):
        return self._id

    def __hash__(self):
        """Generate hash from the node's id.

        WARNING: Obviously this hash doesn't cover all of the node's
        data, but we need nodes to be hashable in order to eliminate
        duplicates in the NodeDB.

        At least the id cannot change after initialization...
        """
        return hash(self.id)

    @property
    def vpn_neighbors(self):
        try:
            vpn_neighbors = []
            for neighbor in self['neighbors']:
                if neighbor['neighbor']['vpn']:
                    vpn_neighbors.append(neighbor)
            return vpn_neighbors
        except TypeError:
            return []

    def export(self):
        """Generate a serializable dict of the node.

        In particular, this replaces any references to other nodes by
        their id to prevent circular references.
        """
        ret = dict(self)
        if "neighbors" in self:
            ret["neighbors"] = []
            for neighbor in self["neighbors"]:
                new_neighbor = {}
                for key, val in neighbor.items():
                    if isinstance(val, Node):
                        new_neighbor[key] = val.id
                    else:
                        new_neighbor[key] = val
                ret["neighbors"].append(new_neighbor)
        return ret
