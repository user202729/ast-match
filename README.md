# ast-match

A library to facilitate easier manipulation of Python AST (abstract syntax tree) objects.

This library allows you to write the syntax in an intuitive way, instead of having to write the names of the internal classes in `ast` module.

For manipulating the internal structure, it's recommended to read through https://docs.python.org/3/library/ast.html to know what kind of nodes may appear in an AST.

### Usage

Import everything (apart from testing purpose it's recommended to avoid `import *`):

```python
from ast_match import *
```

First, note that Python distinguishes between statement and expression, so you need to specify the type explicitly:

```python
>>> expr("a=1")
Traceback (most recent call last):
    ...
AssertionError

>>> stmt("a=1")
<a = 1>
Assign(
  targets=[
    Name(id='a', ctx=Store())],
  value=Constant(value=1))
```

The API somewhat resemble `re` module API:

```python
>>> import re
>>> pattern=re.compile("(?P<last>.*)-1")
>>> match=pattern.fullmatch("7*8-1")
>>> match.groupdict()
{'last': '7*8'}

>>> pattern=to_pattern_mutable(parse_expr("_last-1"))
>>> match=pattern_match(pattern, parse_expr("7*8-1"))
>>> match
{'last': <7 * 8>
BinOp(
  left=Constant(value=7),
  op=Mult(),
  right=Constant(value=8))}
```

There's no direct analog for `re.search` or `re.sub`, but there's support for limited replacement:

```python
>>> pattern=to_pattern_mutable(parse_expr("_last-1"))
>>> pattern_replace_mutable(pattern, {"last": parse_expr("a*b")})
<a * b - 1>
BinOp(
  left=BinOp(
    left=Name(id='a', ctx=Load()),
    op=Mult(),
    right=Name(id='b', ctx=Load())),
  op=Sub(),
  right=Constant(value=1))
```



### Note for Vim users

The code inside strings may not be syntax-highlighted as Python code.

TODO how to fix?

### Note for IPython users

For usage in IPython, the default display of `ast`-module objects is not very nice:

```python
In [19]: ast.parse('for i in range(10): print(i, i+1)')
Out[19]: <ast.Module at 0x7fc4b17d6110>
```

So it's recommended you use the following.

```python
formatter=get_ipython().display_formatter.formatters["text/plain"]
formatter.for_type(ast.AST, lambda o, p, cycle: p.text(ast.dump(o, indent=2)))
#formatter.for_type(ast.AST, lambda o, p, cycle: p.text(prettyrepr(o)))  # alternative, prettier but does not show the internal
#formatter.pop(ast.AST)  # revert
```

Then the display will be more readable:

```python
In [21]: ast.parse('for i in range(10): print(i, i+1)')
Out[21]: 
Module(
  body=[
    For(
      target=Name(id='i', ctx=Store()),
      iter=Call(
        func=Name(id='range', ctx=Load()),
        args=[
          Constant(value=10)],
        keywords=[]),
      body=[
        Expr(
          value=Call(
            func=Name(id='print', ctx=Load()),
            args=[
              Name(id='i', ctx=Load()),
              BinOp(
                left=Name(id='i', ctx=Load()),
                op=Add(),
                right=Constant(value=1))],
            keywords=[]))],
      orelse=[])],
  type_ignores=[])
```
