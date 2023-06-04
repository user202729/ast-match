
To create the documentation (folder structure):

```
# sphinx-quickstart docs --sep -p ast-match -a user202729 -r '' -l en

rm docs/ast_match.rst
sphinx-apidoc --full -o docs ast_match
```

To autobuild the documentation

```
cd docs
sphinx-autobuild . /tmp/_build/ --watch ..
```

To create a tag

```
git tag 0.1.0
git push --tags
```

