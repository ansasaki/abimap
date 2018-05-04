"""Entrypoint used to generate the command line application"""

from smap import symver


def main():
    class C(object):
        """
        Empty class used as a namespace
        """
        pass

    ns = C()

    # Get the arguments parser
    parser = symver.get_arg_parser()

    # Parse arguments
    args = parser.parse_args(namespace=ns)

    # Run command
    ns.func(args)
