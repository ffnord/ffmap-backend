#!/usr/bin/env python3
import argparse
import sys

from ffmap import run_names

class MyAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if self.dest.startswith(("input_", "output_")):
            collection_name = self.dest.split("_")[0] + "s"
            name = self.dest.split("_", 1)[1]
            if not hasattr(namespace, collection_name):
                setattr(namespace, collection_name, [])
            collection = getattr(namespace, collection_name)
            collection.append({
                "name": name,
                "options": {self.metavar.lower(): values}
                           if values is not None else {}
            })
        else:
            raise Exception("Unexpected dest=" + self.dest)

def parser_add_myarg(parser, name, metavar="OPT", help=None):
    parser.add_argument("--" + name,
                        metavar=metavar,
                        type=str,
                        nargs='?',
                        const=None,
                        action=MyAction,
                        help=help)

parser = argparse.ArgumentParser(
    description="""Merge node data from multiple sources and generate
                   various output formats from this data""",
)
input_group = parser.add_argument_group("Inputs", description="""
    Inputs are used in the order given on the command line, where later
    inputs can overwrite attributes of earlier inputs if named equally,
    but the first input encountering a node sets its id, which is
    immutable afterwards.

    The same input can be given multiple times, probably with different
    options.
""")
output_group = parser.add_argument_group("Outputs")
parser_add_myarg(input_group, 'input-alfred', metavar="REQUEST_DATA_TYPE",
                 help="read node details from A.L.F.R.E.D.")
parser_add_myarg(input_group, 'input-wiki', metavar="URL",
                 help="read node details from a Wiki page")
parser_add_myarg(input_group, 'input-batadv', metavar="MESH_INTERFACE",
                 help="add node's neighbors and clients from batadv-vis")
parser_add_myarg(output_group, 'output-d3json', metavar="FILEPATH",
                 help="generate JSON file compatible with ffmap-d3")
parser_add_myarg(output_group, 'output-rrd', metavar="DIRECTORY",
                 help="update RRDs with statistics, one global and one per node")

args = parser.parse_args()

if "inputs" not in args or not args.inputs:
    parser.print_help(sys.stderr)
    sys.stderr.write("\nERROR: No input has been defined!\n")
    sys.exit(1)

if "outputs" not in args or not args.outputs:
    parser.print_help(sys.stderr)
    sys.stderr.write("\nERROR: No output has been defined!\n")
    sys.exit(1)

run_names(inputs=args.inputs, outputs=args.outputs)
