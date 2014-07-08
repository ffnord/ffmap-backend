import importlib

from ffmap.nodedb import NodeDB

def run(inputs, outputs):
    """Fill the database with given inputs and give it to given outputs.

    Arguments:
    inputs -- list of Input instances (with a compatible get_data(nodedb) method)
    outputs -- list of Output instances (with a compatible output(nodedb) method)
    """
    db = NodeDB()
    for input_ in inputs:
        input_.get_data(db)

    for output in outputs:
        output.output(db)

def run_names(inputs, outputs):
    """Fill the database with inputs and give it to outputs, each given
    by names.

    In contrast to run(inputs, outputs), this method expects only the
    names of the modules to use, not instances thereof.
    Arguments:
    inputs -- list of dicts, each dict having the keys "name" with the
              name of the input to use (directory name in inputs/), and
              the key "options" with a dict of input-dependent options.
    outputs -- list of dicts, see inputs.
    """
    input_instances = []
    output_instances = []

    for input_ in inputs:
        module = importlib.import_module(".inputs." + input_["name"], "ffmap")
        input_instances.append(module.Input(**input_["options"]))

    for output in outputs:
        module = importlib.import_module(".outputs." + output["name"], "ffmap")
        output_instances.append(module.Output(**output["options"]))

    run(input_instances, output_instances)
