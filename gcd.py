#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

from aga import *


def mkGcd(typ):
	x = mkRegU(typ)
	y = mkReg(typ, 0)

	rule('swap', (x > y) and (y != 0),
		x=y, y=x
	)
	rule('subtract', (x <= y) and (y != 0),
		y=y-x,
	)






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
