#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2018, University of California, Berkeley
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>

from aga import *


class Testbench(Module):
	def __init__(self):
		super().__init__()
		with self.rule("rl_print_answer") as r:
			r.display("Deep Thought says: Hello, World! The answer is 42.")
			r.finish()


def main():
	circuit = elaborate(Testbench())
	simulate(circuit, max_cycles=10)


if __name__ == '__main__':
	main()
