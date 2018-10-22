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
	def __init__(self, name=None):
		if name is None:
			self.name = self.__class__.__name__
		else:
			self.name = name
		self.state = []
		self.rules = []

	def rule(self, name: str):
		rr = RuleBuilder(name=name)
		self.rules.append(rr)
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


## Elaborate ##
import firrtl

class Elaboration:
	def __init__(self):
		# all the following fields are initialized by the run method
		self.ids = None

	@property
	def _clock(self):
		return firrtl.Ref("clk")
	@property
	def _reset(self):
		return firrtl.Ref("reset")

	def _unique_id(self, prefix):
		if prefix not in self.ids:
			name = prefix
		else:
			counter = 0
			while f"{prefix}_{counter}" in self.ids:
				counter += 1
			name = f"{prefix}_{counter}"
		self.ids.add(name)
		return name

	def run(self, mod: Module):
		assert isinstance(mod, Module)
		# reset global fields
		self.ids = {"clk", "reset"}

		# TODO: check module interface and create ports
		ports = [
			firrtl.Port(name="clk", typ=Clock(), dir=firrtl.PortDir.Input),
			firrtl.Port(name="reset", typ=UInt(1), dir=firrtl.PortDir.Input)
		]

		statements = []

		# generate registers
		for reg in mod.state:
			statements += self.visit(reg)

		# generate (combinational) rule circuits
		for rule in mod.rules:
			statements += self.visit(rule)

		# TODO: generate scheduler

		return firrtl.Circuit(name=mod.name, modules=[
			firrtl.Module(name=mod.name, ports=ports, statements=statements)
		])




	def visit(self, node):
		"""Visit a node."""
		method = 'visit_' + node.__class__.__name__
		visitor = getattr(self, method, self.generic_visit)
		return visitor(node)

	def generic_visit(self, node):
		raise NotImplementedError(f"TODO: visit({node.__class__.__name__})")

	def visit_NoneType(self, _none):
		return ""


	def visit_RuleBuilder(self, node):
		# TODO
		return []


def elaborate(module: Module):
	return Elaboration().run(module)

def simulate(circuit, max_cycles: int):
	ir = firrtl.ToString().visit(circuit)
	print(ir)

	from simulator import Simulator
	use_server = True
	if use_server:
		sim = Simulator.start_remote()
		print("using treadle server...")
	else:
		sim = Simulator.start_local()

	sim.load(ir)
	sim.poke("reset", 1)
	sim.step(1)
	sim.poke("reset", 0)
	sim.step(max_cycles)
