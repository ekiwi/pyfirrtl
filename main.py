from firrtl import *


def ports(**kwargs):
	return [Port(name=name, ty=ty) for name, ty in kwargs]

def module(name, ports, statements):
	return Module(name=name, ports=ports, statements=statements)


def make_circuit():
	return Circuit(name="Gcd", modules=[
		module("Gcd",
			ports(
				clock=Clock(),
				reset=UInt(1),


			   ),
			   []
			   )
	])



if __name__ == "__main__":
	ir = ToString().visit(make_circuit())
	print(ir)