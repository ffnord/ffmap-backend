from .node import Node

class AmbiguityError(Exception):
    """Indicate the ambiguity of identifiers.

    This exception is raised if there is more than one match for a set
    of identifiers.

    Attributes:
    identifiers -- set of ambiguous identifiers
    """

    identifiers = []

    def __init__(self, identifiers):
        self.identifiers = identifiers

    def __str__(self):
        return "Ambiguous identifiers: %s" % ", ".join(self.identifiers)

class NodeDB(dict):
    def add_or_update(self, ids, other=None):
        """Add or update a node in the database.

        Searches for an already existing node and updates it, or adds a new
        one if no existing one is found.  Raises an AmbiguityException if
        more than one different nodes are found matching the criteria.

        Arguments:
        ids -- list of possible identifiers (probably MAC addresses) of the
               node
        other -- dict of values to update in an existing node or add to
                 the new one.  Defaults to None, in which case no values
                 are added or updated, only the aliases of the
                 (possibly freshly created) node are updated.
        """

        # Find existing node, if any
        node = None
        node_id = None
        for id_ in ids:
            if id_ == node_id:
                continue
            if id_ in self:
                if node is not None and node is not self[id_]:
                    raise AmbiguityError([node_id, id_])
                node = self[id_]
                node_id = id_

        # If no node was found, create a new one
        if node is None:
            node = Node(ids[0])

        # Update the node with the given properties using its own update method.
        if other is not None:
            node.deep_update(other)

        # Add new aliases if any
        for id_ in ids:
            self[id_] = node
