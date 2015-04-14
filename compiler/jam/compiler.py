import logging
from io import IOBase

from . import parser
from ..lekvar import lekvar
from ..llvm import emitter as llvm
from ..llvm.builtins import builtins
from ..errors import CompilerError

def _compileFunc(func):
    def f(input, *args):
        try:
            return func(input, *args)
        except CompilerError as err:
            # Format the error and re-raise
            input.seek(0)
            err.format(input.read())
            raise err
    return f

def _compile(input:IOBase, logger):
    # Produce lekvar
    ir = parser.parseFile(input)
    lekvar.verify(ir, builtins(), logger)
    # Emit LLVM
    return llvm.emit(ir, logger)

@_compileFunc
def compileRun(input:IOBase, output:IOBase = None, logger = logging.getLogger()):
    module = _compile(input, logger)
    if output is not None:
        print(llvm.compile(module))
        output.write(llvm.compile(module).decode("UTF-8"))
    return llvm.run(module).decode("UTF-8")

@_compileFunc
def compile(input:IOBase, output:IOBase, logger = logging.getLogger()):
    output.write(llvm.compile(_compile(input, logger)).decode("UTF-8"))


