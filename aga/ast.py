#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

# AST/Runtime

from typing import Optional, List
import kast

# we use almost same types as firrtl
from firrtl import Type, UInt, SInt, Clock, Vector, Field, Bundle
import firrtl

class Bool(type):
	pass

class Node(kast.Node):
	pass

class Wire(Node):
	typ = Type
	name = Optional[str] # optional name **hint**

class Statement(Node):
	pass

class Stop(Statement):
	exit_code = Optional[int]

class PrintF(Statement):
	format_str = str
	vargs = List[Wire]


class Module:
	def __init__(self, name=None):
		if name is None:
			self.name = self.__class__.__name__
		else:
			self.name = name
		self.state = []
		self.rules = []

	def rule(self, name: str):
		assert not any(rr.name == name for rr in self.rules), "Rule names need to be unique"
		rr = Rule(name=name)
		self.rules.append(rr)
		return rr


class Rule:
	def __init__(self, name: str):
		self.name = name
		self.statements = []
		self.guard = firrtl.Literal(value=1, typ=UInt(1))
		self._under_construction = False

	def __enter__(self):
		self._under_construction = True
		return self

	def __exit__(self, type, value, traceback):
		self._under_construction = False

	def display(self, format_str : str, *vargs):
		assert self._under_construction
		self.statements.append(PrintF(format_str=format_str, vargs=list(vargs)))

	def finish(self):
		assert self._under_construction
		self.statements.append(Stop())

