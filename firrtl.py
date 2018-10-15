import kast
from typing import List, Optional
from enum import Enum


class Node(kast.Node):
	pass

## Types ##

class Type(Node):
	pass

class UInt(Type):
	n = Optional[int]

class SInt(Type):
	n = Optional[int]

class Clock(Type):
	pass

class Vector(Type):
	elementtype = Type
	count = int

class Field(Node):
	name = str
	typ = Type

class Bundle(Type):
	fields = List[Field]

## Statement ##

class Statement(Node):
	pass

class Connect(Statement):
	pass


## Modules ##

class PortDir(Enum):
	Input = 0
	Output = 1

class Port(Node):
	name = str
	ty = Type
	dir = PortDir

class Module(Node):
	name = str
	ports = List[Port]
	statements = List[Statement]

class Circuit(Node):
	modules = List[Module]