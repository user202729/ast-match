"""
Main module.
"""

from __future__ import annotations

import ast
from ast_match.pattern import *
from copy import deepcopy
from typing import Union, Iterator, Callable, Optional

def stmt(code: str)->ast.stmt:
	r"""
	Parse code as a statement::

		>>> pp(stmt('a=1'))
		<ast.AST: a = 1>
		>>> pp(stmt('for i in range(5): print(i)'))
		<ast.AST: for i in range(5):
		    print(i)>
	"""
	body=ast.parse(code).body
	assert len(body)==1
	assert isinstance(body[0], ast.stmt)
	return body[0]

def expr(code: str)->ast.expr:
	r"""
	Parse code as an expression::

		>>> pp(expr('a+b'))
		<ast.AST: a + b>
		>>> pp(expr('a=1'))
		Traceback (most recent call last):
			...
		AssertionError
	"""
	statement=stmt(code)
	assert isinstance(statement, ast.Expr)
	return statement.value

def prettyrepr(o: ast.AST|list)->str:
	"""
	Pretty print an ``ast.AST`` object. Return a string.
	The output should not be considered stable.

	Example::

		>>> prettyrepr(stmt('a=1'))
		'<ast.AST: a = 1>'
	"""
	if isinstance(o, list):
		return "[" + ", ".join(prettyrepr(x) for x in o) + "]"
	try: return "<ast.AST: " + ast.unparse(o) + ">"
	except: return "<ast.AST: " + ast.dump(o, indent=2) + ">"

@dataclass
class _Prettyprint:
	repr: str
	def __repr__(self)->str: return self.repr

def pp(o: ast.AST)->_Prettyprint:
	"""
	Pretty print an ``ast.AST`` object (by returning an object whose repr is the specified string).
	This function is mainly for internal pytest doctesting only.

	The output should not be considered stable.

	Example::

		>>> pp(stmt('a=1'))
		<ast.AST: a = 1>
	"""
	return _Prettyprint(prettyrepr(o))

class _Privateconstructonly: pass

_privateconstructonly=_Privateconstructonly()

@dataclass
class Repl:
	"""
	Second argument to :meth:`Pattern.sub` and similar methods.
	"""
	_pattern: Pattern0

	def __init__(self, o: _Privateconstructonly, pattern: Pattern0)->None:
		if o is not _privateconstructonly: raise TypeError("Repl is not constructible directly, use repl() instead")
		self._pattern=pattern

	def __repr__(self)->str:
		return "<Repl: " + ast.dump(self._pattern, indent=2) + ">"


def repl(node: ast.AST)->Repl:
	"""
	Construct a :class:`Repl` object.

	Used as the first argument of :meth:`Pattern.sub` and similar methods.

	The syntax is similar to, but not the same as, :func:`compile`.

	For example::

		>>> pp(compile(stmt('_a=1')).sub(repl(stmt('_a=2')), stmt('b=1')))
		<ast.AST: b = 2>

	Similar to :func:`compile`, you can also use ``BlankNullSequence``::

		>>> pp(compile(stmt('f(__a)*g(__b)')).sub(repl(stmt('h(__a, 0, __b)')), stmt('f(1, 2)*g(3, 4)')))
		<ast.AST: h(1, 2, 0, 3, 4)>
	"""
	node=deepcopy(node)
	return Repl(_privateconstructonly, to_pattern_mutable(node))

@dataclass
class Match:
	"""
	Return type of functions such as :meth:`Pattern.fullmatch`.
	"""
	matching: Matching0

	def __init__(self, *args, **kwargs):
		"""
		Constructor. Example::

			>>> Match({"a": expr("1")})
			Match{'a': <ast.AST: 1>}
			>>> Match(a=expr("1"))
			Match{'a': <ast.AST: 1>}
		"""
		if len(args)==1 and not kwargs:
			assert isinstance(args[0], dict)
			self.matching=args[0]
		else:
			assert not args
			self.matching=dict(**kwargs)

	def __repr__(self):
		"""
		>>> Match({"a": expr("1")})
		Match{'a': <ast.AST: 1>}
		"""
		return "Match{" + ", ".join(
				f"{key!r}: {prettyrepr(value)}" for key, value in self.matching.items()
				) + "}"
	
	def expand(self, o: Repl)->ast.AST:
		"""
		Substitute the matched values into the pattern, and return the result.

		Example::

			>>> m=Match(a=expr("b"))
			>>> m
			Match{'a': <ast.AST: b>}
			>>> pp(m.expand(repl(stmt('_a=1'))))
			<ast.AST: b = 1>

		As they're ``ast.AST`` objects, nestings etc. are properly handled::

			>>> pp(Match(a=expr("1*2"), b=expr("3*4")).expand(repl(expr("_a+_b"))))
			<ast.AST: 1 * 2 + 3 * 4>
			>>> pp(Match(a=expr("1+2"), b=expr("3+4")).expand(repl(expr("_a*_b"))))
			<ast.AST: (1 + 2) * (3 + 4)>
			>>> pp(Match(body=stmt("print(i)")).expand(repl(stmt("for i in range(n): _body"))))
			<ast.AST: for i in range(n):
			    print(i)>

		"""
		return pattern_replace_mutable(
				deepcopy(o._pattern), self.matching)

	def __getitem__(self, key: str)->ast.AST|list:
		"""
		>>> pp(Match(a=expr("1"))["a"])
		<ast.AST: 1>
		"""
		return self.matching[key]

	def group(self, key: str)->ast.AST|list:
		"""
		>>> pp(Match(a=expr("1")).group("a"))
		<ast.AST: 1>
		"""
		return self.matching[key]

@dataclass
class Pattern:
	pattern: Pattern0

	def __init__(self, o: _Privateconstructonly, pattern: Pattern0)->None:
		if o is not _privateconstructonly: raise TypeError("Pattern is not constructible directly, use compile() instead")
		self._pattern=pattern

	def fullmatch(self, text: ast.AST)->Optional[Match]:
		r"""
		Match this pattern against the provided text::

			>>> compile(expr("_last-1")).fullmatch(expr("7*8-1"))
			Match{'last': <ast.AST: 7 * 8>}
		"""
		match=pattern_match(self._pattern, text)
		if match is None: return None
		return Match(match)

	def finditer(self, text: ast.AST)->Iterator[Match]:
		"""
		Find all matching occurrences.

		Example::

			>>> [*compile(expr("_a*_b")).finditer(expr("1*2+3*4"))]
			[Match{'a': <ast.AST: 1>, 'b': <ast.AST: 2>}, Match{'a': <ast.AST: 3>, 'b': <ast.AST: 4>}]
		"""
		if isinstance(text, list):
			for item in text:
				yield from self.finditer(item)

		elif isinstance(text, ast.AST):
			# check top level match
			matching=self.fullmatch(text)
			if matching is not None:
				yield matching

			# check children
			for field_name, text0 in ast.iter_fields(text):
				if isinstance(text0, ast.AST):  # TODO what if text0 is list?
					yield from self.finditer(text0)

		else:
			assert False, (self, text)

	def sub(self, replace: Union[ast.AST, Repl, Callable[[ast.AST, Match], ast.AST]], text: ast.AST)->ast.AST:
		"""
		Replace all occurrences.

		Parameters like ``count`` or functionalities like ``re.subn`` is not supported.

		The *replace* parameter can be an AST, a pattern, or a function that takes the whole match and a :class:`Match` object and returns an AST.

		Example::

			>>> pp(compile(expr("1")).sub(expr("2"), expr("1+5+7+1")))
			<ast.AST: 2 + 5 + 7 + 2>
			>>> pp(compile(expr("1")).sub(lambda whole, _matching: Match(x=whole).expand(repl(expr("f(_x)"))), expr("1+5+7+1")))
			<ast.AST: f(1) + 5 + 7 + f(1)>
			>>> pp(compile(expr("_x*_y")).sub(repl(expr("_y*_x")), expr("2*3+4*5")))
			<ast.AST: 3 * 2 + 5 * 4>
		"""
		#if isinstance(text, list):
		#	return [self.sub(replace, item) for item in text]

		if isinstance(text, ast.AST):
			# check top level match
			matching=self.fullmatch(text)
			if matching is not None:
				if isinstance(replace, ast.AST):
					return replace
				elif isinstance(replace, Repl):
					return matching.expand(replace)
				else:
					assert callable(replace)
					return replace(text, matching)

			# check children
			for field_name, text0 in ast.iter_fields(text):
				if isinstance(text0, ast.AST):
					setattr(text, field_name, self.sub(replace, text0))

			return text

		else:
			assert False

	def __repr__(self)->str:
		return "<Pattern: " + ast.dump(self._pattern, indent=2) + ">"


def compile(node: ast.AST)->Pattern:
	r"""
	Compile an ``ast.AST`` object to a pattern.

	Example::

		>>> compile(stmt('_a=1'))
		<Pattern: Assign(
		  targets=[
		    Blank(var='a')],
		  value=Constant(value=1))>
		>>> compile(expr('_a+_b'))
		<Pattern: BinOp(left=Blank(var='a'), op=Add(), right=Blank(var='b'))>

	A variable prefixed with ``_`` denotes a "blank" i.e. placeholder.
	The concept of ``Blank`` comes from Mathematica.

	Similarly there's a ``BlankNullSequence``.
	While a ``Blank`` can only match one item::

		>>> compile(expr("f(_a)")).fullmatch(expr("f(1)"))
		Match{'a': <ast.AST: 1>}
		>>> compile(expr("f(_a)")).fullmatch(expr("f(1, 2)"))

	A ``BlankNullSequence`` can match zero or more items::

		>>> compile(expr("f(__a)")).fullmatch(expr("f(1)"))
		Match{'a': [<ast.AST: 1>]}
		>>> compile(expr("f(__a)")).fullmatch(expr("f()"))
		Match{'a': []}
		>>> compile(expr("f(__a)")).fullmatch(expr("f(1, 2)"))
		Match{'a': [<ast.AST: 1>, <ast.AST: 2>]}

	Similarly:

		>>> compile(stmt("for i in range(10): _a")).fullmatch(stmt("for i in range(10): 1; 2"))
		>>> compile(stmt("for i in range(10): __a")).fullmatch(stmt("for i in range(10): 1; 2"))
		Match{'a': [<ast.AST: 1>, <ast.AST: 2>]}
	"""
	node=deepcopy(node)
	return Pattern(_privateconstructonly, to_pattern_mutable(node))

