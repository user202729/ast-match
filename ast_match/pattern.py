## there's some legacy code here. Will refactor some time...

from __future__ import annotations
from dataclasses import dataclass
import ast
from typing import Optional, Any
import copy

@dataclass(frozen=True)
class Blank:
	"""
	represent a place holder in a pattern. Var is the variable name.
	"""
	var: str

@dataclass(frozen=True)
class BlankNullSequence:
	var: str

def name_to_blank_or_verbatim_mut(node: ast.AST)->Optional[Blank|BlankNullSequence|ast.AST]:
	"""
	Convert a name node to a blank-like node. Also detect names that represent "verbatim".

	Example::

		>>> name_to_blank_or_verbatim_mut(ast.Name(id='x'))
		>>> name_to_blank_or_verbatim_mut(ast.Name(id='_x'))
		Blank(var='x')
		>>> name_to_blank_or_verbatim_mut(ast.Name(id='__x'))
		BlankNullSequence(var='x')

	It's possible to specify "verbatim"::

		>>> ast.dump(name_to_blank_or_verbatim_mut(ast.Name(id='_v_x')))
		"Name(id='_x')"
	"""
	if not isinstance(node, ast.Name): return None
	s: str=node.id
	if s.startswith('_'):
		if s.startswith('__'):
			return BlankNullSequence(var=s[2:])
		elif s.startswith('_v_'):
			node.id=s[2:]
			return node
		else:
			return Blank(var=s[1:])
	else:
		return None

def node_to_blank_or_verbatim_mut(node: ast.AST)->Optional[Blank|BlankNullSequence|ast.AST]:
	"""
	Same as :func:`name_to_blank_or_verbatim_mut`, but also handle Expr(value=Name(id=...)) nodes::

		>>> node_to_blank_or_verbatim_mut(ast.Name(id='_x'))
		Blank(var='x')
		>>> node_to_blank_or_verbatim_mut(ast.Expr(ast.Name(id='_x')))
		Blank(var='x')
		>>> ast.dump(node_to_blank_or_verbatim_mut(ast.Name(id='_v_x')))
		"Name(id='_x')"
		>>> ast.dump(node_to_blank_or_verbatim_mut(ast.Expr(ast.Name(id='_v_x'))))
		"Expr(value=Name(id='_x'))"
	"""
	tmp=name_to_blank_or_verbatim_mut(node)
	if tmp is not None: return tmp
	if isinstance(node, ast.Expr):
		tmp=name_to_blank_or_verbatim_mut(node.value)
		if tmp is not None:
			if isinstance(tmp, ast.AST):
				node.value=tmp
				return node
			return tmp
	return None

def scan_node_to_pattern(node: ast.AST)->None:
	"""
	internal method, scan through the tree to convert parsed Python syntax tree to pattern tree.
	"""
	assert isinstance(node, ast.AST), node

	for field_name, child in ast.iter_fields(node):
		if isinstance(child, list):
			for i, x in enumerate(child):
				tmp=node_to_blank_or_verbatim_mut(x)
				if tmp is not None:
					child[i]=tmp
				else:
					scan_node_to_pattern(x)

			if len(child)==1 and isinstance(child[0], BlankNullSequence):
				setattr(node, field_name, child[0])

			elif any(isinstance(x, BlankNullSequence) for x in child):
				raise NotImplementedError(f"BlankNullSequence together with another item is not implemented -- {child=}")

		elif isinstance(child, ast.AST):
			tmp=node_to_blank_or_verbatim_mut(child)
			if tmp is not None:
				setattr(node, field_name, tmp)
			else:
				scan_node_to_pattern(child)

		else:
			pass

Pattern0=ast.AST

def to_pattern_mutable(node: ast.AST)->Pattern0:
	scan_node_to_pattern(node)
	return node

Matching0=dict[str, ast.AST]

def merge_matching(a: Optional[Matching0], b: Optional[Matching0])->Optional[Matching0]:
	if a is None or b is None: return None
	a=dict(a)
	for key, value in b.items():
		if key in a and a[key]!=value: return None
		a[key]=value
	return a

def pattern_match(pattern: Pattern0|list, tree: ast.AST|list)->Optional[Matching0]:
	if isinstance(pattern, Blank) or isinstance(pattern, BlankNullSequence):
		if isinstance(pattern, Blank): assert not isinstance(tree, list)
		elif isinstance(pattern, BlankNullSequence): assert isinstance(tree, list)
		return {pattern.var: tree}
	if type(pattern)!=type(tree): return None

	result: Optional[Matching0]={}

	if isinstance(pattern, list):
		assert isinstance(tree, list)
		if len(pattern)!=len(tree): return None
		for pattern0, tree0 in zip(pattern, tree):
			result=merge_matching(result, pattern_match(pattern0, tree0))
			if result is None: return None

	elif isinstance(pattern, ast.AST):
		for field_name, pattern0 in ast.iter_fields(pattern):
			result=merge_matching(result, pattern_match(pattern0, getattr(tree, field_name)))
			if result is None: return None

	else:
		if pattern!=tree: return None

	return result


def pattern_replace_mutable(pattern: Any, replacement: Matching0)->Any:
	"""
	might or might not modify the input pattern.
	The result is *returned*. don't rely on the input pattern being changed to the correct output.

	note. For convenience, result might not be ast.AST if the input is not
	"""
	if isinstance(pattern, Blank) or isinstance(pattern, BlankNullSequence):
		result=replacement[pattern.var]
		if isinstance(pattern, Blank): assert not isinstance(result, list)
		elif isinstance(pattern, BlankNullSequence): assert isinstance(result, list)
		return result

	elif isinstance(pattern, list):
		return [pattern_replace_mutable(item, replacement) for item in pattern]  # type: ignore

	elif isinstance(pattern, ast.AST):
		for field_name, pattern0 in ast.iter_fields(pattern):
			setattr(pattern, field_name, pattern_replace_mutable(pattern0, replacement))
		return pattern

	else:
		return pattern
