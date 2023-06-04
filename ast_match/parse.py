from __future__ import annotations
import ast

def parse_statement(code: str)->ast.stmt:
	body=ast.parse(code).body
	assert len(body)==1
	assert isinstance(body[0], ast.stmt)
	return body[0]

def parse_expr(code: str)->ast.expr:
	statement=parse_statement(code)
	assert isinstance(statement, ast.Expr)
	return statement.value
