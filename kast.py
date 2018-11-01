#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2017, 2018, Kevin Laeufer <laeufer@eecs.berkeley.edu>

# This software may be modified and distributed under the terms
# of the BSD license. See the LICENSE file for details.

# support for typed IR nodes

from typing import Union, Optional, List, Tuple, Iterable

def _isinstance(obj, typ) -> bool:
	typ_name = str(typ)
	is_typing = typ_name.startswith('typing.')
	if not is_typing:
		return isinstance(obj, typ)
	name = typ_name.split('.')[1].split('[')[0]
	if name == 'Union':
		return any(_isinstance(obj, aa) for aa in typ.__args__)
	elif name == 'List':
		(et,) = typ.__args__
		return isinstance(obj, list) and all(_isinstance(ii, et) for ii in obj)
	elif name == 'Tuple':
		return isinstance(obj, tuple) and all(_isinstance(ii, aa) for ii,aa in zip(obj, typ.__args__))
	else:
		raise NotImplementedError(f"_isinstance({obj}, {typ})")

def _is_optional(typ) -> bool:
	return(str(typ).startswith('typing.Union') and
		   any(aa is type(None) for aa in typ.__args__))

def get_fields_of_class(cls):
	""" returns the fields of a single class """
	# this relies on https://www.python.org/dev/peps/pep-0520
	# and Python 3.6 (see Note in PEP520)
	return {n:v for n,v in cls.__dict__.items() if not n[0] == '_'}

def get_fields(cls):
	""" returns fields of the class and all ancestor classes """
	fields = get_fields_of_class(cls)
	while len(cls.__bases__) > 0 and cls.__bases__[0] not in [Node, object]:
		new_fields = [get_fields_of_class(b) for b in cls.__bases__]
		fields_available = [len(ff) > 0 for ff in new_fields]
		assert sum(fields_available) < 2, "multiple inheritance is not supported ... too lazy"
		ii = fields_available.index(True) if sum(fields_available) > 0 else 0
		cls = cls.__bases__[ii]
		# only include base class fields if they have not been overwritten
		for name, value in new_fields[ii].items():
			if name not in fields:
				fields[name] = value
	return fields

def parse_args(names, args, kwargs):
	aa = { ff: aa for ff, aa in zip(names, args) }
	assert set(aa.keys()) & set(kwargs.keys()) == set()
	aa.update(kwargs)
	return aa

def is_type_list(ll):
	return isinstance(ll, list) and all(type(t) == type for t in ll)
def is_str_list(ll):
	return isinstance(ll, list) and all(type(t) == str for t in ll)

def matches_types(types, tt):
	if tt in types: return True
	if str(tt).startswith('typing.List[') and tt.__args__[0] in types: return True
	if isinstance(tt, Optional): return matches_types(types, tt.field_type)
	return False

class Node:
	""" type checking replacement for ast.AST"""
	def __init__(self, *args, **kwargs):
		fields = get_fields(type(self))
		field_names = fields.keys()
		aa = parse_args(field_names, args, kwargs)
		# check completeness
		for name, value in fields.items():
			if not name in aa and not _is_optional(value):
				raise TypeError("Missing value for field `{}`".format(name))
		# check types
		for name, value in aa.items():
			if not _isinstance(value, fields[name]):
				raise TypeError("Field `{}` requires values of type `{}` not `{}`".format(
					name, fields[name], type(value)))
		# accept field values
		for name in field_names:
			object.__setattr__(self, name, aa.get(name, None))
		# fake _fields
		object.__setattr__(self, "_fields", field_names)
	def __setattr__(self, name, value):
		raise AttributeError("kAST nodes are immutable!")
	def map(self, fun):
		new_values = {}
		for name, old in iter_fields(self):
			if old is None: continue
			if isinstance(old, list):
				new = list(filter_none(fun(o) for o in old))
			elif isinstance(old, tuple):
				new = tuple(filter_none(fun(o) for o in old))
			else:
				new = fun(old)
			if new is None: continue
			new_values[name] = new
		return self.__class__(**new_values)
	def apply(self, fun):
		for _, val in iter_fields(self):
			if val is None: continue
			if isinstance(val, list) or isinstance(val, tuple):
				for vv in val: fun(vv)
			else:
				fun(val)
	def set(self, **kwargs):
		if len(kwargs) < 1: return self
		field_names = set(self._fields)
		assert set(kwargs.keys()).issubset(set(self._fields))
		new_values = { name: kwargs.get(name, self.__getattribute__(name)) for name in self._fields }
		return self.__class__(**new_values)
	def __str__(self):
		desc = self.__class__.__name__ + "("
		fields = []
		for name in self._fields:
			if getattr(self, name, None) is None: continue
			fields.append(str(getattr(self, name)))
		return self.__class__.__name__ + "(" + ", ".join(fields) + ")"
	def __repr__(self): return str(self)

# code bellow copied + modified from Python3 ast library
def iter_fields(node: Node):
	for field in node._fields:
		try:
			yield field, getattr(node, field)
		except AttributeError:
			pass

class NodeVisitor:
	def visit(self, node):
		method = 'visit_' + node.__class__.__name__
		getattr(self, method, self.generic_visit)(node)

	def generic_visit(self, node):
		if isinstance(node, Node):
			node.apply(self.visit)

def filter_none(iter: Iterable) -> Iterable:
	return (ii for ii in iter if ii is not None)

class NodeTransformer:
	def visit(self, node):
		method = 'visit_' + node.__class__.__name__
		return getattr(self, method, self.generic_visit)(node)

	def generic_visit(self, node):
		if isinstance(node, Node):
			return node.map(self.visit)
		else:
			return node