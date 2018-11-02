#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

import firrtl
from .ast import *

def default(maybe, dd):
	if maybe is None: return dd
	else: return maybe

def priority_mux(signals):
	front = signals[0]
	if len(signals) == 1:
		return front[1]
	else:
		return firrtl.Mux(front[0], front[1], priority_mux(signals[1:]))

def priority_encoder(inputs):
	T = UInt(len(inputs))
	vectors = [T(1<<ii) for ii in reversed(range(len(inputs)))]
	signals = list(zip(inputs, vectors)) + [(UInt(1)(0), T(0))]
	out = priority_mux(signals)
	return [firrtl.Extract(out, ii, ii) for ii in reversed(range(len(inputs)))]

from functools import reduce
def _and(a,b):
	return firrtl.BinOp(op=firrtl.Bop.And, e1=a, e2=b)
def _or(a,b):
	return firrtl.BinOp(op=firrtl.Bop.Or, e1=a, e2=b)
def _not(a):
	return firrtl.UnOp(op=firrtl.Uop.Not, e=a)
# should behave the same as `priority_encoder`, TODO: formally verify (at least for a couple of instances)
def priority_encoder_2(inputs):
	assert len(inputs) >= 1
	return [inputs[0]] + [_and(inputs[ii+1], _not(reduce(_and, inputs[:ii+1])))
		for ii in range(len(inputs) - 1)
	]

class Elaboration(kast.NodeTransformer):
	def __init__(self):
		self._can_fire = {}
		self._firing = {}
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

	def _wire(self, ref, typ):
		return firrtl.WireDeclaration(name=ref.name, typ=typ)

	def _connect(self, lhs, rhs):
		return firrtl.Connect(lhs=lhs, rhs=rhs)

	def run(self, mod: Module):
		assert isinstance(mod, Module)
		# reset global fields
		self._can_fire = {}
		self._firing = {}

		for rule in mod.rules:
			self._can_fire[rule] = Wire(typ=UInt(1), name=f"{mod.name}_{rule.name}_can_fire")
			self._firing[rule] = Wire(typ=UInt(1), name=f"{mod.name}_{rule.name}_firing")


		# TODO: find state in module, analyze rules and methods as to what state the modify and what they update

		# TODO: generate ports for methods

		ports = [
			firrtl.Port(name="clk", typ=Clock(), dir=firrtl.PortDir.Input),
			firrtl.Port(name="reset", typ=UInt(1), dir=firrtl.PortDir.Input)
		]

		statements = []

		# generate (combinational) rule circuits
		for rule in mod.rules:
			statements += self.visit(rule)

		# generate scheduler
		scheduler = priority_encoder_2([self._can_fire[rule] for rule in mod.rules])
		for ii, rule in enumerate(mod.rules):
			statements.append(self._connect(self._firing[rule], scheduler[ii]))


		return firrtl.Circuit(name=mod.name, modules=[
			firrtl.Module(name=mod.name, ports=ports, statements=statements)
		])

	def visit_Rule(self, node):
		assert isinstance(node.name, str)
		self.can_fire, self.firing = self._can_fire[node], self._firing[node]
		stmts  = [self._connect(self.can_fire, node.guard_expr)]
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

def unique_id(prefix, ids):
	if prefix not in ids:
		name = prefix
	else:
		counter = 0
		while f"{prefix}_{counter}" in ids:
			counter += 1
		name = f"{prefix}_{counter}"
	return name

class FindRegistersAndWires(kast.NodeVisitor):
	def __int__(self):
		self.regs_and_wires = set()
	def run(self, node):
		self.regs_and_wires = set()
		self.visit(node)
		return self.regs_and_wires
	def visit_Wire(self, node):
		if isinstance(node, Wire):
			self.regs_and_wires.add(node)
	def visit_Register(self, node):
		if isinstance(node, Register):
			self.regs_and_wires.add(node)


class DeclareRegistersAndWires(kast.NodeTransformer):
	""" declares gaa.Register and gaa.Wire and inserts references for them """
	def __init__(self):
		self.ids = {}
		self._FindRegistersAndWires = FindRegistersAndWires()

	@staticmethod
	def name(mod, node):
		if node.name is None:
			if isinstance(node, Register):
				return f"{mod.name}_reg"
			else:
				return f"{mod.name}_wire"
		else:
			return node.name

	@staticmethod
	def reg(reg: Register, name: str, reset: str, clk: str):
		reset = None if reg.reset is None else firrtl.Reset(enable=firrtl.Ref(reset), value=reg.typ(reg.reset))
		return firrtl.Register(name=name, typ=reg.typ, clock=firrtl.Ref(clk), reset=reset)

	@staticmethod
	def wire(wire: Wire, name: str):
		return firrtl.WireDeclaration(name=name, typ=wire.typ)

	def run(self, mod, reset: str, clk: str, regs_and_wires=None):
		assert isinstance(mod, firrtl.Module)
		if regs_and_wires is None:
			regs_and_wires = self._FindRegistersAndWires.run(mod)
		reserved_ids = { pp.name for pp in mod.ports }
		decls = []
		for node in regs_and_wires:
			name = unique_id(self.name(mod, node), reserved_ids)
			reserved_ids.add(name)
			self.ids[node] = firrtl.Ref(name)
			if isinstance(node, Register):
				decls.append(self.reg(node, name, reset, clk))
			elif isinstance(node, Wire):
				decls.append(self.wire(node, name))
			else:
				raise TypeError(f"unexpected type: {type(node)} of {node}")
		stmts = [self.visit(stmt) for stmt in mod.statements]
		return mod.set(statements=decls + stmts)

	def visit_Wire(self, node):
		if isinstance(node, Wire):
			return self.ids[node]
		return node

	def visit_Register(self, node):
		if isinstance(node, Register):
			return self.ids[node]
		return node