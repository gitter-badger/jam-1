import os
import logging
import tempfile
from contextlib import contextmanager
from functools import partial
from abc import abstractmethod as abstract
from subprocess import check_output

from ..lekvar import lekvar
from ..errors import *

from . import bindings as llvm
from .builtins import LLVMType

def emit(module:lekvar.Module, logger = logging.getLogger()):
    State.logger = logger.getChild("llvm")
    llvm.State.logger = State.logger.getChild("bindings")

    with State.begin("main", logger):
        module.emit()

    State.logger.info("LLVM output: {}".format(State.module.verify(llvm.FailureAction.PrintMessageAction, None)))
    return State.module

def compile(module:llvm.Module):
    return module.toString()

def run(module:llvm.Module):
    #TODO: Do this properly
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(compile(module))
        f.flush()

    try:
        return check_output(["lli", f.name])
    finally:
        os.remove(f.name)

class State:
    @classmethod
    @contextmanager
    def begin(cls, name:str, logger:logging.Logger):
        cls.logger = logger

        cls.self = None
        cls.builder = llvm.Builder.new()
        cls.module = llvm.Module.fromName(name)
        cls.main = []
        yield
        main_type = llvm.Function.new(llvm.Int.new(32), [], False)
        main = cls.module.addFunction("main", main_type)

        entry = main.appendBlock("entry")
        with cls.blockScope(entry):
            for func in cls.main:
                call = lekvar.Call("", [])
                call.function = func
                call.emitValue()

            return_value = llvm.Value.constInt(llvm.Int.new(32), 0, False)
            cls.builder.ret(return_value)

    @classmethod
    @contextmanager
    def blockScope(cls, block:llvm.Block):
        previous_block = cls.builder.position
        cls.builder.positionAtEnd(block)
        yield
        cls.builder.positionAtEnd(previous_block)

    @classmethod
    @contextmanager
    def selfScope(cls, self:llvm.Value):
        previous_self = cls.self
        cls.self = self
        yield
        cls.self = previous_self

    @classmethod
    def getTempName(self):
        return "temp"


def main_call(func:lekvar.Function):
    call = lekvar.Call("", [])
    call.function = func
    return call

# Abstract extensions

lekvar.BoundObject.llvm_value = None
lekvar.Function.llvm_return = None

# Extension abstract methods apparently don't work
#@abstract
#def Object_emitValue(self, state:State) -> llvm.Value:
#    pass
#lekvar.Object.emitValue = Object_emitValue

#@abstract
#def Type_emitType(self, state:State) -> llvm.Type:
#    pass
#lekvar.Type.emitType = Type_emitType
#lekvar.Type.llvm_type = None

#
# Tools
#

def resolveName(scope:lekvar.BoundObject):
    # Resolves the name of a scope, starting with a extraneous .
    name = ""
    while scope.bound_context is not None:
        name = "." + scope.name + name
        scope = scope.bound_context.scope
    return "lekvar" + name

# Implements

# For this that don't emit anything
def blank_emitValue(self):
    return None
lekvar.Comment.emitValue = blank_emitValue

#
# class Reference
#

def Reference_emit(self):
    return self.value.emit()
lekvar.Reference.emit = Reference_emit

def Reference_emitValue(self):
    return self.value.emitValue()
lekvar.Reference.emitValue = Reference_emitValue

def Reference_emitType(self):
    return self.value.emitType()
lekvar.Reference.emitType = Reference_emitType

def Reference_emitAssignment(self):
    return self.value.emitAssignment()
lekvar.Reference.emitAssignment = Reference_emitAssignment

#
# class Attribute
#

def Attribute_emitValue(self):
    self.attribute.bound_context.scope.emit()
    return self.attribute.emitValue(self.value.emitAssignment())
lekvar.Attribute.emitValue = Attribute_emitValue

#
# class Literal
#

def Literal_emitValue(self):
    type = self.type.emitType()

    if type == LLVM_MAP["String"]:
        return State.builder.globalString(self.data, State.getTempName())
    else:
        raise InternalError("Not Implemented")
lekvar.Literal.emitValue = Literal_emitValue

#
# class Variable
#

lekvar.Variable.llvm_context_index = -1

def Variable_emit(self):
    if self.llvm_value is not None or self.llvm_context_index >= 0: return

    if isinstance(self.bound_context.scope, lekvar.Class):
        self.bound_context.scope.emit()
    else:
        type = self.type.emitType()
        name = resolveName(self)
        self.llvm_value = State.builder.alloca(type, name)
lekvar.Variable.emit = Variable_emit

def Variable_emitValue(self, value=None):
    self.emit()

    if self.llvm_context_index >= 0:
        print(self.name)
        if value is None:
            value = State.builder.structGEP(State.self, 0, State.getTempName())
        return State.builder.load(State.builder.structGEP(value, self.llvm_context_index, State.getTempName()), State.getTempName())
    elif self.llvm_value is not None:
        return State.builder.load(self.llvm_value, State.getTempName())
    else:
        raise InternalError()
lekvar.Variable.emitValue = Variable_emitValue

def Variable_emitAssignment(self):
    self.emit()

    if self.llvm_value is not None:
        return self.llvm_value

    #context = State.builder.load(State.self, State.getTempName())
    self_value = State.builder.structGEP(State.self, 0, State.getTempName())
    return State.builder.structGEP(self_value, self.llvm_context_index, State.getTempName())
lekvar.Variable.emitAssignment = Variable_emitAssignment

#
# class Assignment
#

def Assignment_emitValue(self):
    value = self.value.emitValue()

    variable = self.variable.emitAssignment()
    State.builder.store(value, variable)
lekvar.Assignment.emitValue = Assignment_emitValue

#
# class Module
#

def Module_emit(self):
    if self.llvm_value is not None: return

    self.llvm_value = self.main.emitValue()
    State.main.append(self.main)

    for child in self.context.children.values():
        child.emit()
lekvar.Module.emit = Module_emit

#
# class Call
#

def Call_emitValue(self):
    called = self.function.emitValue()

    if isinstance(self.function, lekvar.Function):
        if len(self.function.closed_context.children):
            arguments = [self.function.emitContext()]
        else:
            context_type = self.function.llvm_closure_type or llvm.Int.new(8)
            arguments = [llvm.Value.null(context_type)]
    else:
        arguments = []
    arguments += [val.emitValue() for val in self.values]

    # Get the llvm function type
    function_type = llvm.cast(llvm.cast(called.type, llvm.Pointer).element_type, llvm.Function)

    # Check the return type
    if function_type.return_type.kind == llvm.TypeKind.VoidTypeKind:
        name = ""
    else:
        name = State.getTempName()
    return State.builder.call(called, arguments, name)
lekvar.Call.emitValue = Call_emitValue

#
# class Return
#

def Return_emitValue(self):
    exit = self.function.llvm_value.getLastBlock()
    if self.value is None:
        State.builder.br(exit)
    else:
        value = self.value.emitValue()
        State.builder.store(value, self.function.llvm_return)
        State.builder.br(exit)
lekvar.Return.emitValue = Return_emitValue

#
# class Context
#

lekvar.Context.llvm_type = None

def Context_emitType(self):
    if self.llvm_type is not None: return self.llvm_type

    types = []
    for index, child in self.children.items():
        child.llvm_context_index = index
        types.append(child.resolveType().emitType())

    self.llvm_type = llvm.Struct.new(types, False)

    return self.llvm_type
lekvar.Context.emitType = Context_emitType

#
# class DependentType
#

lekvar.DependentType.llvm_type = None

def DependentType_emitType(self):
    if self.llvm_type is None:
        if self.target is None:
            raise InternalError("Invalid dependent type target")
        else:
            self.llvm_type = self.target.emitType()
    return self.llvm_type
lekvar.DependentType.emitType = DependentType_emitType

#
# class Function
#

lekvar.Function.llvm_closure_type = None
lekvar.Function.llvm_context = None

def Function_emit(self):
    if self.dependent: return
    if self.llvm_value is not None: return

    if len(self.closed_context.children) > 0:
        self.llvm_value = 0 # Temporarily set llvm_value to something so this function isn't emitted twice
        self.bound_context.scope.emit()
        self.llvm_closure_type = self.closed_context.emitType()
    else:
        self.llvm_closure_type = llvm.Type.void_p()

    name = resolveName(self)
    func_type = self.resolveType().emitType(self.llvm_closure_type)
    self.llvm_value = State.module.addFunction(name, func_type)

    entry = self.llvm_value.appendBlock("entry")
    exit = self.llvm_value.appendBlock("exit")

    with State.blockScope(entry):
        self.emitBody()
        State.builder.br(exit)

    with State.blockScope(exit):
        self.emitReturn()

lekvar.Function.emit = Function_emit

def Function_emitBody(self):
    # Allocate context
    self.llvm_context = State.builder.alloca(self.llvm_closure_type, "context")
    State.builder.store(self.llvm_value.getParam(0), self.llvm_context)
    self.emitPreContext()
    with State.selfScope(self.llvm_context):

        # Allocate Arguments
        for index, arg in enumerate(self.arguments):
            val = self.llvm_value.getParam(index + 1)
            arg.llvm_value = State.builder.alloca(arg.type.emitType(), resolveName(arg))
            State.builder.store(val, arg.llvm_value)

        self.emitPostContext()

        # Emit instructions
        for instruction in self.instructions:
            instruction.emitValue()
lekvar.Function.emitBody = Function_emitBody

def Function_emitPostContext(self):
    # Allocate Return Variable
    if self.type.return_type is not None:
        self.llvm_return = State.builder.alloca(self.type.return_type.emitType(), "return")
lekvar.Function.emitPostContext = Function_emitPostContext

def Function_emitReturn(self):
    if self.llvm_return is not None:
        val = State.builder.load(self.llvm_return, State.getTempName())
        State.builder.ret(val)
    else:
        State.builder.retVoid()
lekvar.Function.emitReturn = Function_emitReturn

def Function_emitValue(self):
    self.emit()
    return self.llvm_value
lekvar.Function.emitValue = Function_emitValue

def Function_emitPreContext(self):
    pass
lekvar.Function.emitPreContext = Function_emitPreContext

def Function_emitContext(self):
    pass
lekvar.Function.emitContext = Function_emitContext

#
# Contructor
#

def Constructor_emitPreContext(self):
    #context = State.builder.load(context, State.getTempName())
    self_var = State.builder.structGEP(self.llvm_context, 0, State.getTempName())
    self_val = State.builder.load(State.builder.alloca(self.bound_context.scope.bound_context.scope.emitType(), State.getTempName()), State.getTempName())
    State.builder.store(self_val, self_var)
lekvar.Constructor.emitPreContext = Constructor_emitPreContext

def Constructor_emitPostContext(self):
    pass
lekvar.Constructor.emitPostContext = Constructor_emitPostContext

def Constructor_emitReturn(self):
    context = State.builder.structGEP(self.llvm_context, 0, State.getTempName())
    value = State.builder.load(context, State.getTempName())
    State.builder.ret(value)
lekvar.Constructor.emitReturn = Constructor_emitReturn

def Constructor_emitContext(self):
    self.emit()
    return llvm.Value.null(self.llvm_closure_type)
lekvar.Constructor.emitContext = Constructor_emitContext

#
# class FunctionType
#

def FunctionType_emitType(self, context_type = None):
    if context_type is None:
        arguments = []
    else:
        arguments = [context_type]

    arguments += [type.emitType() for type in self.arguments]

    if self.return_type is not None:
        return_type = self.return_type.emitType()
    else:
        return_type = llvm.Type.void()
    return llvm.Function.new(return_type, arguments, False)
lekvar.FunctionType.emitType = FunctionType_emitType

#
# class ExternalFunction
#

lekvar.ExternalFunction.llvm_closure_type = None

def ExternalFunction_emit(self):
    if self.llvm_value is not None: return

    func_type = self.type.emitType()
    self.llvm_value = State.module.addFunction(self.external_name, func_type)
lekvar.ExternalFunction.emit = ExternalFunction_emit

def ExternalFunction_emitValue(self):
    self.emit()
    return self.llvm_value
lekvar.ExternalFunction.emitValue = ExternalFunction_emitValue

#
# class Method
#

def Method_emit(self):
    if self.llvm_value is not None: return

    if isinstance(self.bound_context.scope, lekvar.Class):
        self.bound_context.scope.emit()
    self.llvm_value = 0

    for overload in self.overload_context.children.values():
        overload.emit()
lekvar.Method.emit = Method_emit

#
# class Class
#

lekvar.Class.llvm_type = None

def Class_emit(self):
    if self.llvm_type is not None: return

    var_types = []
    for child in self.instance_context.children.values():
        if isinstance(child, lekvar.Variable):
            child.llvm_context_index = len(var_types)
            var_types.append(child.type.emitType())

    self.llvm_type = llvm.Struct.new(var_types, False)

    for child in self.instance_context.children.values():
        child.emit()

lekvar.Class.emit = Class_emit

def Class_emitType(self):
    self.emit()
    return self.llvm_type
lekvar.Class.emitType = Class_emitType

#
# class LLVMType
#

LLVM_MAP = None

def LLVMType_emitType(self):
    global LLVM_MAP
    if LLVM_MAP is None:
        LLVM_MAP = {
            "String": llvm.Pointer.new(llvm.Int.new(8), 0),
            "Int8": llvm.Int.new(8),
            "Int16": llvm.Int.new(16),
            "Int32": llvm.Int.new(32),
            "Int64": llvm.Int.new(64),
            "Float16": llvm.Float.half(),
            "Float32": llvm.Float.float(),
            "Float64": llvm.Float.double(),
        }
    return LLVM_MAP[self.name]
LLVMType.emitType = LLVMType_emitType
