import os.path
import string
import bytevm.sys as sys
import argparse
import logging
import bytevm.execfile as bex
import enum

from pycore import dataparser as dp
from .vm import TrackerVM, Op
from .tstr import tstr

def log(var, i=1):
    print(repr(var), file=sys.stderr, flush=True)

import pudb
brk =  pudb.set_trace

class ExecFile(bex.ExecFile):

    def exec_code_object(self, code, env):
        self.start_i = 0
        vm = TrackerVM()
        try:
            self.cmp_output = []
            log(">> %s" % sys.argv[1], 0)
            v = vm.run_code(code, f_globals=env)
            chars = [o for o in vm.cmp_trace if hasattr(o.opA, 'x')] # these are tstrs.
            chars = sorted(chars, key=lambda x: x.opA.x())
            for o in chars:
                self.cmp_output.append(o)
            return v
        except Exception as e:
            print(e)

    def cmdline(self, argv):
        parser = argparse.ArgumentParser(
            prog="pychains",
            description="Find valid inputs for the given program.",
        )
        parser.add_argument(
            '-m', dest='module', action='store_true',
            help="prog is a module name, not a file name.",
        )
        parser.add_argument(
            '-v', '--verbose', dest='verbose', action='store_true',
            help="trace the execution of the bytecode.",
        )
        parser.add_argument(
            'prog',
            help="The program to run.",
        )
        parser.add_argument(
            'args', nargs=argparse.REMAINDER,
            help="Arguments to pass to the program.",
        )
        args = parser.parse_args(argv)

        level = logging.DEBUG if args.verbose else logging.WARNING
        logging.basicConfig(level=level)

        self.run_python_file(args.prog, [args.prog] + [tstr(i) for i in args.args])
