## there's some legacy code here. Will refactor some time...

from __future__ import annotations
from dataclasses import dataclass
import ast

@dataclass(frozen=True)
class Blank:
	"""
	represent a place holder in a pattern. Var is the variable name.
	"""
	var: str

def name_represent_blank(node: ast.AST)->bool:
	return isinstance(node, ast.Name) and node.id.startswith("_")

def blank_from_name(node: ast.AST)->Blank:
	assert name_represent_blank(node)
	assert isinstance(node, ast.Name)
	return Blank(node.id[1:])
def ast_is_leaf(pattern: Pattern0)->bool:
	return (
				isinstance(pattern, (str, int, float,
					)) or pattern is None # ast.For.type_comment
				)

def scan_node_to_pattern(node: ast.AST)->None:
	"""
	internal method, scan through the tree to convert parsed Python syntax tree to pattern tree.
	"""
	assert isinstance(node, ast.AST), node

	# special case: body node
	if (
			hasattr(node, "body") and
			len(node.body)==1 and isinstance(node.body[0], ast.Expr) and  # type: ignore
			name_represent_blank(node.body[0].value)  # type: ignore
			):
		node.body=blank_from_name(node.body[0].value)  # type: ignore

	# normal node
	for field_name, child in ast.iter_fields(node):
		if name_represent_blank(child):
			assert getattr(node, field_name) is child
			setattr(node, field_name, blank_from_name(child))

		elif isinstance(child, list):
			for i, x in enumerate(child):
				if name_represent_blank(x):
					child[i]=blank_from_name(x)
				else:
					scan_node_to_pattern(x)

		elif isinstance(child, ast.AST): scan_node_to_pattern(child)

		else:
			assert (
					ast_is_leaf(child) or isinstance(child, Blank) # converted in the body case above
					), (child, node)

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

def pattern_match(pattern: Pattern0, tree: ast.AST)->Optional[Matching0]:
	if isinstance(pattern, Blank):
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
		assert ast_is_leaf(pattern), (pattern, tree)
		if pattern!=tree: return None

	return result


def pattern_replace_mutable(pattern: Pattern0, replacement: Matching0)->ast.AST:
	"""
	might or might not modify the input pattern.
	The result is *returned*. don't rely on the input pattern being changed to the correct output.

	note. For convenience, result might not be ast.AST if the input is not
	"""
	if isinstance(pattern, Blank): return replacement[pattern.var]

	elif isinstance(pattern, list):
		return [pattern_replace_mutable(item, replacement) for item in pattern]  # type: ignore

	elif isinstance(pattern, ast.AST):
		for field_name, pattern0 in ast.iter_fields(pattern):
			setattr(pattern, field_name, pattern_replace_mutable(pattern0, replacement))
		return pattern

	else:
		assert ast_is_leaf(pattern), pattern
		return pattern
