#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

# AST/Runtime

from typing import Optional, List, Tuple
import kast

# we use almost same types as firrtl
from firrtl import Type, UInt, SInt, Clock, Vector, Field, Bundle, Expr
import firrtl


# patch type with literal constructor
Type.__call__ = lambda self, val: firrtl.Literal(value=val, typ=self)

# patch expr with combinators
# TODO: propagate size/type

Expr.__and__ = lambda self, other: firrtl.BinOp(op=firrtl.Bop.And, e1=self, e2=other)
Expr.__sub__ = lambda self, other: firrtl.BinOp(op=firrtl.Bop.Sub, e1=self, e2=other)
Expr.__invert__ = lambda self: firrtl.UnOp(op=firrtl.Uop.Not, e=self)
Expr.__lt__ = lambda self, other: firrtl.Cmp(op=firrtl.Cop.LT, e1=self, e2=other)
Expr.__le__ = lambda self, other: firrtl.Cmp(op=firrtl.Cop.LE, e1=self, e2=other)
Expr.__eq__ = lambda self, other: firrtl.Cmp(op=firrtl.Cop.EQ, e1=self, e2=other)
Expr.__ne__ = lambda self, other: firrtl.Cmp(op=firrtl.Cop.NE, e1=self, e2=other)
Expr.__ge__ = lambda self, other: firrtl.Cmp(op=firrtl.Cop.GE, e1=self, e2=other)
Expr.__gt__ = lambda self, other: firrtl.Cmp(op=firrtl.Cop.GT, e1=self, e2=other)


class Node(kast.Node):
	pass

class Statement(Node):
	pass

class Stop(Statement):
	exit_code = Optional[int]

class PrintF(Statement):
	format_str = str
	vargs = List[Expr]

class Wire(Expr):
	typ = Type
	name = Optional[str] # optional name **hint**

class Register(Expr):
	typ = Type
	reset = Optional[int]

def Reg(T: Type, value: int):
	return Register(typ=T, reset=value)
def RegU(T: Type):
	return Register(typ=T)

class Module:
	def __init__(self, name=None):
		if name is None:
			self.name = self.__class__.__name__
		else:
			self.name = name
		self.state = []
		self.rules = []
		self.methods = []

	def _assert_unique_name(self, name: str):
		assert not any(rr.name == name for rr in self.rules), "Rule names need to be unique"

	def rule(self, name: str):
		self._assert_unique_name(name)
		rr = Rule(mod=self, name=name)
		self.rules.append(rr)
		return rr

	def action(self, name: str, **kwargs):
		self._assert_unique_name(name)
		# TODO: expose as class argument!
		rr = ActionMethod(mod=self, name=name, args=[(k,v) for k,v in kwargs.items()])
		self.methods.append(rr)
		return rr

	def value(self, T: Type, name: str):
		self._assert_unique_name(name)
		# TODO: expose as class argument!
		rr = ValueMethod(mod=self, name=name, T=T)
		self.methods.append(rr)
		return rr

class RuleBase:
	def __init__(self, mod: Module, name: str):
		self.mod = mod
		self.name = name
		self.guard_expr = UInt(1)(1) # TODO: change to bool
		self._under_construction = False

	def __enter__(self):
		self._under_construction = True
		return self

	def __exit__(self, type, value, traceback):
		self._under_construction = False

	def guard(self, expr: Expr):
		self.guard_expr &= expr
		return self

class Rule(RuleBase):
	def __init__(self, mod: Module, name: str):
		super().__init__(mod=mod, name=name)
		self.name = name
		self.statements = []
		self.updates = {}

	def display(self, format_str : str, *vargs):
		assert self._under_construction
		self.statements.append(PrintF(format_str=format_str, vargs=list(vargs)))
		return self

	def finish(self):
		assert self._under_construction
		self.statements.append(Stop())
		return self

	def update(self, **kwargs):
		for name, val in kwargs.items():
			state = self.mod.__getattribute__(name)
			assert state not in self.updates
			self.updates[state] = val
		return self

class ActionMethod(Rule):
	def __init__(self, mod: Module, name: str, args: List[Tuple[str,Type]]):
		super().__init__(mod=mod, name=name)
		self.args = [Wire(name=name,typ=typ) for name,typ in args]
		for aa in self.args:
			self.__setattr__(aa.name, aa)

class ValueMethod(RuleBase):
	def __init__(self, mod: Module, name: str, T: Type):
		super().__init__(mod=mod, name=name)
		self.return_type = T
		self.return_expr = None
	def ret(self, expr: Expr):
		assert self.return_expr is None, "return cannot be called twice!"
		self.return_expr = expr
		return self

