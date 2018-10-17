import kast
from typing import List, Optional
from enum import Enum


class Node(kast.Node):
	pass

## Types ##

class Type(Node):
	pass

class UInt(Type):
	n = Optional[int]

class SInt(Type):
	n = Optional[int]

class Clock(Type):
	pass

class Vector(Type):
	elementtype = Type
	count = int

class Field(Node):
	name = str
	typ = Type

class Bundle(Type):
	fields = List[Field]

## Expressions ##
class Expression(Node):
	pass
	#ty = Type

class Ref(Expression):
	name = str

class Mux(Expression):
	sel = Expression
	a = Expression
	b = Expression

class ValidIf(Expression):
	valid = Expression
	a = Expression


## Statement ##

class Statement(Node):
	pass


class Connect(Statement):
	lhs = Ref
	rhs = Expression

## Modules ##

class PortDir(Enum):
	Input = 0
	Output = 1

class Port(Node):
	name = str
	ty = Type
	dir = PortDir

class Module(Node):
	name = str
	inputs = List[Field]
	outputs = List[Field]
	statements = List[Statement]

class Circuit(Node):
	name = str
	modules = List[Module]


## To String ##
class ToString:

	def visit(self, node: Node) -> str:
		"""Visit a node."""
		method = 'visit_' + node.__class__.__name__
		visitor = getattr(self, method, self.generic_visit)
		return visitor(node)

	def generic_visit(self, node: Node):
		raise NotImplementedError(f"TODO: visit({node.__class__.__name__})")

	# Types
	def visit_Field(self, node: Field) -> str:
		return f"{node.name}: {self.visit(node.typ)}"
	def visit_UInt(self, node: Field) -> str:
		if node.n is None: return "UInt"
		else: return f"UInt<{node.n}>"
	def visit_SInt(self, node: Field) -> str:
		if node.n is None: return "SInt"
		else: return f"SInt<{node.n}>"
	def visit_Clock(self, _node: Clock):
		return "Clock"

	def visit_Circuit(self, node: Circuit) -> str:
		return f"circuit {node.name} :\n" + "\n".join(self.visit(mod) for mod in node.modules)

	def visit_Module(self, node: Module) -> str:
		ir  = [f"  module {node.name} :"]
		ir += [f"    input {self.visit(ii)}" for ii in node.inputs]
		ir += [f"    output {self.visit(ii)}" for ii in node.outputs]
		ir += [f"    {self.visit(stmt)}" for stmt in node.statements]
		return "\n".join(ir)

	def visit_Connect(self, node: Connect) -> str:
		return f"{self.visit(node.lhs)} <= {self.visit(node.rhs)}"

	# Expressions
	def visit_Ref(self, node: Ref):
		return node.name