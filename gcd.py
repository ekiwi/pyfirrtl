#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

from aga import *


class Gcd(Module):
	def __init__(self, typ: Type):
		super().__init__(
			x = RegU(typ),
			y = Reg(typ, 0)
		)
		with self.rule("swap").if(x > y and y != 0) as r:
			r.update(x=y, y=x)
		with self.rule("subtract").if(x <= y and y != 0) as r:
			r.update(y=y-x)
		with self.method(Action, "start", a=typ, b=typ).if(y == 0) as m:
			m.update(x=a, y=b)
		with self.method(typ, "result").if(y == 0) as m:
			m.ret(x)



def mkGcd(typ):
	x = mkRegU('x', typ)
	y = mkReg('y', typ, 0)

	rule('swap', (x > y) and (y != 0),
		x=y, y=x
	)
	rule('subtract', (x <= y) and (y != 0),
		y=y-x,
	)
	method(Action, 'start'

	)


def main():
	print("Hello World")

	# elaborate

	# simulate for N cycles



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