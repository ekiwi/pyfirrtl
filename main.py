from firrtl import *
from typing import Tuple

def out(name: str, ty: Type) -> Tuple[str, Field]:
	return 'out', Field(name=name, typ=ty)

def inp(name: str, ty: Type) -> Tuple[str, Field]:
	return 'inp', Field(name=name, typ=ty)

def ports(*args: Tuple[str, Field]) -> List[Tuple[str, Field]]:
	return list(args)

def module(name: str, pps: List[Tuple[str, Field]], statements: List[Statement]):
	inputs  = [p for di, p in pps if di == 'inp']
	outputs = [p for di, p in pps if di == 'out']
	return Module(name=name, inputs=inputs, outputs=outputs, statements=statements)

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