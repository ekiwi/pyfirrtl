#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

# Atomic Guarded Actions

from typing import Optional, List
import kast

# we use almost same types as firrtl
from firrtl import Type, UInt, SInt, Clock, Vector, Field, Bundle

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
	def __init__(self):
		self._state = []
		self._rules = []

	def rule(self, name: str):
		rr = RuleBuilder(name=name)
		self._rules.append(rr)
		return rr


class RuleBuilder:
	def __init__(self, name: str):
		self.name = name
		self._statements = []
		self._under_construction = False

	def __enter__(self):
		self._under_construction = True
		return self

	def __exit__(self, type, value, traceback):
		self._under_construction = False

	def display(self, format_str : str, *vargs):
		assert self._under_construction
		self._statements.append(PrintF(format_str=format_str, vargs=list(vargs)))

	def finish(self):
		assert self._under_construction
		self._statements.append(Stop())

def elaborate(module: Module):
	print(f"TODO: implement elaborate({module})")

def simulate(circuit, max_cycles: int):
	print(f"TODO: implement simulate({circuit}, {max_cycles})")
