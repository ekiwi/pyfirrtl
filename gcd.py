#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

from gaa import *


class Gcd(Module):
	def __init__(self, T: Type):
		super().__init__()
		self.x = x = RegU(T)
		self.y = y = Reg(T, 0)
		is_active = y != T(0)

		with self.rule("swap").guard(x > y & is_active) as r:
			r.update(x=y, y=x)
		with self.rule("subtract").guard(x <= y & is_active) as r:
			r.update(y=y-x)
		with self.action("start", a=T, b=T).guard(~is_active) as m:
			m.update(x=m.a, y=m.b)
		with self.value(T, "result").guard(~is_active) as m:
			m.ret(x)

def main():
	T = UInt(32)
	circuit = elaborate(Gcd(T))
	ir = get_firrtl(circuit)
	print(ir)

	from simulator import Simulator
	sim = Simulator.start_remote()
	sim.load(ir)

"""
interface I_GCD;
	method Action start (int a, int b);
	method int result();
endinterface

module mkGCD(I_GCD);
	Reg  # (int) x <- mkRegU;
	Reg  # (int) y <- mkReg(0);

	rule swap((x > y) & & (y != 0));
		x <= y;	y <= x;
	endrule
	rule subtract((x <= y) & & (y != 0));
		y <= y – x;
	endrule
	method Action start(int a, int b) if (y == 0);
		x <= a; y <= b;
	endmethod
	method int result() if (y == 0);
		return x;
	endmethod
endmodule
"""

if __name__ == '__main__':
	main()