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

def assign(lhs: Ref, rhs: Expr) -> Connect:
	return Connect(lhs=lhs, rhs=rhs)

def _not(e: Expr) -> Expr:
	return UnOp(op=Uop.Not, e=e)

def make_circuit():
	return Circuit(name="Inv", modules=[
		module("Inv",
			ports(inp('clk', Clock()), inp('reset', UInt(1)), inp('in', UInt(1)), out('out', UInt(1))),
			   [assign(Ref('out'), _not(Ref('in')))]
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