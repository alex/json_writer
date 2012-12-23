import sys

try:
    import simplejson as json
except ImportError:
    import json

try:
    from json_writer import JSONWriter
except ImportError:
    pass

from . import utils


class Person(object):
    def __init__(self, name):
        self.name = name


def dump_json(data):
    return json.dumps([
        {"name": p.name}
        for p in data
    ])


def dump_json_writer(data):
    w = JSONWriter()
    with w.array():
        for p in data:
            with w.object():
                w.write_key("name")
                w.write(p.name)


def main(argv):
    data = [
        Person(i)
        for i in xrange(250000)
    ]
    if argv[1] == "json":
        func = dump_json
    elif argv[1] == "json_writer":
        func = dump_json_writer
    utils.run_benchmark(func, data)

if __name__ == "__main__":
    main(sys.argv)
