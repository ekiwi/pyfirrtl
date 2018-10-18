#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>


from firrtl import *
from typing import Tuple, Optional

def out(name: str, ty: Type) -> Port:
	return Port(name=name, typ=ty, dir=PortDir.Output)

def inp(name: str, ty: Type) -> Port:
	return Port(name=name, typ=ty, dir=PortDir.Input)

def ports(*args: Port) -> List[Port]:
	return list(args)

def module(name: str, pps: List[Port], statements: List[Statement]):
	default = [inp('clk', Clock()), inp('reset', UInt(1))]
	return Module(name=name, ports=default+pps, statements=statements)

def assign(lhs: Ref, rhs: Expr) -> Connect:
	return Connect(lhs=lhs, rhs=rhs)

def _not(e: Expr) -> Expr:
	return UnOp(op=Uop.Not, e=e)

def reg(name: str, typ: Type, reset=None):
	if reset is None:
		return Register(name=name, typ=typ, clock=Ref("clk"))
	else:
		return Register(name=name, typ=typ, clock=Ref("clk"), reset=Reset(Ref("reset"), reset))

def make_circuit():
	return Circuit(name="Inv", modules=[
		module("Inv",
			ports(inp('in', UInt(1)), out('out', UInt(1))),
			   [
					reg("delay", UInt(1), Ref('in')),
					assign(Ref('delay'), _not(Ref('in'))),
					assign(Ref('out'), Ref('delay'))
			   ]
			   )
	])



if __name__ == "__main__":
	circuit = make_circuit()

	import os
	out_dir = os.path.join('/home', 'kevin', 'd', 'treadle')
	filename = os.path.join(out_dir, f'{circuit.name.lower()}.fir')
	ir = ToString().visit(circuit)

	with open(filename, 'w') as ff:
		ff.write(ir + '\n')
	print(ir)