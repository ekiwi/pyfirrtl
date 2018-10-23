#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

from aga import *


###############################################################################

"""
class Testbench(Module):
	def __init__(self):
		super().__init__()
		with self.rule("rl_print_answer") as r:
			r.display("Deep Thought says: Hello, World! The answer is 42.")
			r.finish()
"""

###############################################################################

class DeepThought(Module):
	def __init__(self, T):
		super().__init__()
		with self.value(T, "getAnswer") as r:
			r.ret(T(42))

class Testbench(Module):
	def __init__(self, T):
		super().__init__()
		self.deepThought = DeepThought(T)
		with self.rule("rl_print_answer") as r:
			x = self.deepThought.getAnswer()
			r.display("Deep Thought says: Hello, World! The answer is %d.", x)
			r.finish()


###############################################################################

def main():
	T = UInt(32)
	circuit = elaborate(Testbench(T))
	simulate(circuit, max_cycles=10)


if __name__ == '__main__':
	main()
