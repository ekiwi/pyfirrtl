import kast
from typing import List, Optional, Union
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
class Expr(Node):
	pass
	#ty = Type

class Ref(Expr):
	name = str

class Mux(Expr):
	sel = Expr
	a = Expr
	b = Expr

class ValidIf(Expr):
	valid = Expr
	a = Expr

class PrimOp(Expr):
	pass

class Bop(Enum):
	Add = 0
	Sub = 1
	Mul = 2
	Div = 3
	Rem = 4
	And = 5
	Or = 6
	Xor = 7
	Cat = 8
class BinOp(PrimOp):
	op = Bop
	e1 = Expr
	e2 = Expr

class Cop(Enum):
	EQ = 0
	NE = 1
	LT = 2
	GT = 3
	LE = 4
	GE = 5
class Cmp(PrimOp):
	op = Cop
	e1 = Expr
	e2 = Expr

class Uop(Enum):
	AsUInt  = 0
	AsSInt  = 1
	AsClock = 2
	ArithmeticToSigned = 3
	Neg = 4
	Not = 5
class UnOp(PrimOp):
	op = Uop
	e = Expr

class Pad(PrimOp):
	e = Expr
	n = int

class ShiftLeft(PrimOp):
	""" shl or dynamic shl depending on type of n """
	e = Expr
	n = Union[Expr, int]

class ShiftRight(PrimOp):
	""" shr or dynamic shr depending on type of n """
	e = Expr
	n = Union[Expr, int]

class Extract(PrimOp):
	e = Expr
	hi = int
	lo = int

class Head(PrimOp):
	e = Expr
	n = int

class Tail(PrimOp):
	e = Expr
	n = int

## Statement ##

class Statement(Node):
	pass


class Connect(Statement):
	lhs = Ref
	rhs = Expr

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
def camelCase(name) -> str:
	return name[:1].lower() + name[1:]

class ToString:

	def visit(self, node):
		"""Visit a node."""
		method = 'visit_' + node.__class__.__name__
		visitor = getattr(self, method, self.generic_visit)
		return visitor(node)

	def generic_visit(self, node):
		raise NotImplementedError(f"TODO: visit({node.__class__.__name__})")

	# Types
	def visit_Field(self, node):
		return f"{node.name}: {self.visit(node.typ)}"
	def visit_UInt(self, node):
		if node.n is None: return "UInt"
		else: return f"UInt<{node.n}>"
	def visit_SInt(self, node):
		if node.n is None: return "SInt"
		else: return f"SInt<{node.n}>"
	def visit_Clock(self, _node: Clock):
		return "Clock"

	def visit_Circuit(self, node):
		return f"circuit {node.name} :\n" + "\n".join(self.visit(mod) for mod in node.modules)

	def visit_Module(self, node):
		ir  = [f"  module {node.name} :"]
		ir += [f"    input {self.visit(ii)}" for ii in node.inputs]
		ir += [f"    output {self.visit(ii)}" for ii in node.outputs]
		ir += [f"    {self.visit(stmt)}" for stmt in node.statements]
		return "\n".join(ir)

	def visit_Connect(self, node):
		return f"{self.visit(node.lhs)} <= {self.visit(node.rhs)}"

	# Expressions
	def visit_Ref(self, node):
		return node.name
	def visit_BinOp(self, node):
		e1, e2 = self.visit(node.e1), self.visit(node.e2)
		return f"{str(node.op).lower()}({e1}, {e2})"
	def visit_Cmp(self, node):
		e1, e2 = self.visit(node.e1), self.visit(node.e2)
		op = {'NE': 'neq', 'LE': 'leq', 'GE': 'geq'}.get(node.op, camelCase(node.op.name))
		return f"{op}({e1}, {e2})"
	def visit_UnOp(self, node):
		op = {'ArithmeticToSigned': 'cvt'}.get(node.op, camelCase(node.op.name))
		return f"{op}({self.visit(node.e)})"
	def visit_Pad(self, node):
		assert node.n >= 0
		return f"pad({self.visit(node.e)}, {node.n})"
	def visit_ShiftLeft(self, node):
		e = self.visit(node.e)
		if isinstance(node.n, int):
			assert node.n >= 0
			return f"shl({e}, {node.n})"
		else:
			return f"dshl({e}, {self.visit(node.n)})"
	def visit_ShiftRight(self, node):
		e = self.visit(node.e)
		if isinstance(node.n, int):
			assert node.n >= 0
			return f"shr({e}, {node.n})"
		else:
			return f"dshr({e}, {self.visit(node.n)})"
	def visitExtract(self, node):
		assert node.lo >= 0
		assert node.hi >= node.lo
		return f"bits({self.visit(node.e)}, {node.hi}, {node.lo})"
	def visit_Head(self, node):
		assert node.n >= 0
		return f"head({self.visit(node.e)}, {node.n})"
	def visit_Tail(self, node):
		assert node.n >= 0
		return f"tail({self.visit(node.e)}, {node.n})"