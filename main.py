from firrtl import *
from typing import Tuple

def out(name: str, ty: Type) -> Port:
	return Port(name=name, ty=ty, dir=PortDir.Output)

def inp(name: str, ty: Type) -> Port:
	return Port(name=name, ty=ty, dir=PortDir.Input)

def ports(*args: Port) -> List[Port]:
	return list(args)

def module(name: str, ports: List[Port], statements: List[Statement]):
	return Module(name=name, ports=ports, statements=statements)

def assign(lhs: Ref, rhs: Expression) -> Connect:
	return Connect(lhs=lhs, rhs=rhs)

def make_circuit():
	return Circuit(name="Inv", modules=[
		module("Inv",
			ports(inp('clk', Clock()), inp('reset', UInt(1)), inp('in', UInt(1)), out('out', UInt(1))),
			   [assign(Ref('out'), Ref('in'))]
			   )
	])



if __name__ == "__main__":
	ir = ToString().visit(make_circuit())
	print(ir)