#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

import firrtl
from .ast import *

class NodeVisitor:
	def visit(self, node):
		"""Visit a node."""
		method = 'visit_' + node.__class__.__name__
		visitor = getattr(self, method, self.generic_visit)
		return visitor(node)

	def generic_visit(self, node):
		raise NotImplementedError(f"TODO: visit({node.__class__.__name__})")

	def visit_NoneType(self, _none):
		return ""

def default(maybe, dd):
	if maybe is None: return dd
	else: return maybe

class Elaboration(NodeVisitor):
	def __init__(self):
		# all the following fields are initialized by the run method
		self.ids = None
		self.can_fire = None
		self.firing = None

	@property
	def _clock(self):
		return firrtl.Ref("clk")
	@property
	def _reset(self):
		return firrtl.Ref("reset")

	@staticmethod
	def _can_fire(rule):
		assert isinstance(rule, Rule)
		return f"{rule.name}_can_fire"

	@staticmethod
	def _firing(rule):
		assert isinstance(rule, Rule)
		return f"{rule.name}_firing"

	def _ids(self, *vargs):
		return [self._unique_id(ii) for ii in vargs]

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

	def _wire(self, ref, typ):
		return firrtl.WireDeclaration(name=ref.name, typ=typ)

	def _connect(self, lhs, rhs):
		return firrtl.Connect(lhs=lhs, rhs=rhs)

	def run(self, mod: Module):
		assert isinstance(mod, Module)
		# reset global fields
		self.ids = {"clk", "reset"}
		self.can_fire = None
		self.firing = None

		# prevent rule names to be used for anything else
		for rule in mod.rules:
			self.ids.add(self._firing(rule))
			self.ids.add(self._can_fire(rule))


		# TODO: find state in module, analyze rules and methods as to what state the modify and what they update

		# TODO: generate ports for methods

		ports = [
			firrtl.Port(name="clk", typ=Clock(), dir=firrtl.PortDir.Input),
			firrtl.Port(name="reset", typ=UInt(1), dir=firrtl.PortDir.Input)
		]



		statements = []

		# try to find registers
		public_attr = ((ii, getattr(mod, ii)) for ii in dir(mod) if not ii.startswith("__"))
		reg_names = {}
		for reg_name, reg in (ii for ii in public_attr if isinstance(ii[1], Register)):
			name = self._unique_id(f"{mod.__class__.__name__}_{reg_name}")
			reg_names[Reg] = firrtl.Ref(name)
			reset = None if reg.reset is None else firrtl.Reset(enable=self._reset,value=reg.typ(reg.reset))
			statements += [firrtl.Register(name=name, typ=reg.typ, clock=self._clock, reset=reset)]

		# generate (combinational) rule circuits
		for rule in mod.rules:
			statements += self.visit(rule)

		# generate scheduler
		#assert len(mod.rules) <= 1, "cannot schedule multiple rules yet"
		print("WARNING: priority encoder needed!")
		for rule in mod.rules:
			statements.append(
				self._connect(firrtl.Ref(self._firing(rule)),
							  firrtl.Ref(self._can_fire(rule)))
			)


		return firrtl.Circuit(name=mod.name, modules=[
			firrtl.Module(name=mod.name, ports=ports, statements=statements)
		])

	def visit_Rule(self, node):
		assert isinstance(node.name, str)
		name = node.name
		self.can_fire = firrtl.Ref(self._can_fire(node))
		self.firing   = firrtl.Ref(self._firing(node))
		stmts  = [self._wire(self.can_fire, UInt(1)),
				  self._wire(self.firing, UInt(1)),
				  self._connect(self.can_fire, node.guard_expr)]
		stmts += [self.visit(st) for st in node.statements]

		self.can_fire = self.firing = None
		return stmts

	def visit_Stop(self, node):
		exit_code = default(node.exit_code, 0)
		return firrtl.Stop(clock=self._clock, condition=self.firing,
						   exit_code=exit_code)

	def visit_PrintF(self, node):
		return firrtl.PrintF(clock=self._clock, condition=self.firing,
							 format_str=node.format_str, vargs=node.vargs)

	def visit_Register(self, node, name):
		print(f"TODO: {node} : {name}")
		return []

