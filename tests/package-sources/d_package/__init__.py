"""this package - d - depends on the package s.

loading it depends on where the current working directory of interpreter is.
and really nothing default (without changing the code in d itself)
can make it load s from the package's own directory.
everything is loaded with respect to current interpreter session -- pythonpath, sys.path its' working directory etc.
(dynamic scoping instead of lexical)

so, the first idea does not apply here..."""
