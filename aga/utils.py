#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

from .ast import *
from .elaboration import Elaboration
import firrtl

def elaborate(module: Module):
	return Elaboration().run(module)

def get_firrtl(circuit):
	return firrtl.ToString.visit(circuit)

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
