# ast-match

## **Note**: This library is unmaintained.

A few other interesting libraries:
* https://pypi.org/project/meta/
* https://libcst.readthedocs.io/en/latest/
* https://stackoverflow.com/q/768634/5267751 and links within

------

A library to facilitate easier manipulation of Python AST (abstract syntax tree) objects.

This library allows you to write the syntax in an intuitive way, instead of having to write the names of the internal classes in `ast` module.

For manipulating the internal structure, it's recommended to read through https://docs.python.org/3/library/ast.html to know what kind of nodes may appear in an AST.

It's recommended to read through these at least once (as well as linked documentations at the bottom of the page) at least once,
it will save you lots of time later on.

### Limitations

This module does not allow you to manipulate the tree in *all possible* ways. For that you still need to tinker with the AST itself.

Some behaviors might be unexpected: for example, the pattern `f(__l)` will match `f(1, 2)` as expected, but it will not match `f(a=1)`.

### Related packages

https://greentreesnakes.readthedocs.io/en/latest/examples.html#real-projects

### Usage

Import everything (apart from testing purpose it's recommended to avoid `import *`):

```python
>>> from ast_match import *
>>> from pprint import pprint

```

First, note that Python distinguishes between statement and expression, so you need to specify the type explicitly:

```python
>>> expr("a=1")
Traceback (most recent call last):
    ...
AssertionError

>>> pp(stmt("a=1"))
<ast.AST: a = 1>

```

Here the `pp` function used to "pretty-print" the resulting `ast.AST` object. If you use IPython you may want to refer to the section below for automatic pretty-printing.

The API somewhat resemble `re` module API:

<table>
<tr>
<th>

`re` module

</th>
<th>

`ast_match` module

</th>
</tr>
<tr>
<td>

```python
>>> import re
>>> pattern=re.compile("(?P<last>.*)-1")
>>> match=pattern.fullmatch("7*8-1")
>>> match.groupdict()
{'last': '7*8'}

```

</td>
<td> 

```python
>>> from ast_match import *
>>> pattern=compile(expr("_last-1"))
>>> match=pattern.fullmatch(expr("7*8-1"))
>>> match
Match{'last': <ast.AST: 7 * 8>}

```

</td>
</tr>
<tr>
<td>

```python
>>> pattern=re.compile(r"(?P<x>\d+)\*(?P<y>\d+)")
>>> pattern.sub(r"\g<y>*\g<x>", "1*2+3*4")
'2*1+4*3'

```

</td>
<td> 

```python
>>> pattern=compile(expr("_x * _y"))
>>> pp(pattern.sub(repl(expr("_y*_x")), expr("1*2+3*4")))
<ast.AST: 2 * 1 + 4 * 3>

```

</td>
</tr>
<tr>
<td>

```python
>>> pattern=re.compile(r"(?P<a>\d+)\*(?P<b>\d+)")
>>> pprint([*pattern.finditer("1*2+3*4")])
[<re.Match object; span=(0, 3), match='1*2'>,
 <re.Match object; span=(4, 7), match='3*4'>]

```

</td>
<td> 

```python
>>> pattern=compile(expr("_a*_b"))
>>> pprint([*pattern.finditer(expr("1*2+3*4"))])
[Match{'a': <ast.AST: 1>, 'b': <ast.AST: 2>},
 Match{'a': <ast.AST: 3>, 'b': <ast.AST: 4>}]

```

</td>
</tr>
</table>


### Remark

In order to execute an `ast.AST`-like object,
you can use the built-in `compile()` function like `compile(ast.Expression(t), "filename", "eval")`.

There are also some helper functions such as `compile_exec_ast`.

### Note for Vim users

The code inside strings may not be syntax-highlighted as Python code.

To fix, consider adding the following to `.vim/after/syntax/python.vim`:

```vim
syn region  pythonSpecialInclude1
			\ start=+\(expr\|stmt\)(r\?\z(['"]\)+ end=+\z1)+ keepend
			\ contains=pythonSpecialIncludeInner1

syn region  pythonSpecialIncludeInner1
			\ start=+\z(['"]\)\zs+ end=+\ze\z1+ keepend
			\ contained contains=TOP
```

You may want to test on some Python code as follows (the part inside `expr` should be highlighted as Python code instead of string)

```python
expr("lambda x: 1")
expr(r"lambda x: 1")
expr("""
for i in range(5):
	pass
""")
expr(r"""
for i in range(5):
	pass
""")
expr('lambda x: 1')
stmt('for i in range(5): pass')
```

For functions other than `expr` or `stmt` it should still be highlighted as string:

```python
f('for i in range(5): pass')
f(r'for i in range(5): pass')
```


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

It may also be desirable to put the code into `.ipython/profile_default/startup/` or similar so that it's run automatically when IPython starts.
