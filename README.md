python-json-patch-ext
=====================

[![PyPI version](https://img.shields.io/pypi/v/jsonpatchext.svg)](https://pypi.python.org/pypi/jsonpatchext/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/jsonpatchext.svg)](https://pypi.python.org/pypi/jsonpatch/)

Applying JSON Patches in Python
-------------------------------

This module extends the Python [jsonpatch](https://github.com/stefankoegl/python-json-patch) module to 
add 'check', 'mutate' and 'merge' operations.

See source code for examples

* Website: https://github.com/RangelReale/python-json-patch-ext
* Repository: https://github.com/RangelReale/python-json-patch-ext.git
* Documentation: https://python-json-patch-ext.readthedocs.org/
* PyPI: https://pypi.python.org/pypi/jsonpatchext


### Example

```python
def StartsWithComparator(current, compare):
    if current.startswith(compare):
        msg = '{0} ({1}) does not starts with {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))

def RemoveLastMutator(current, value):
    return current[:-1]

patch = JsonPatchExt([
    {'op': 'add', 'path': '/foo', 'value': {'bar': 'barvalue'}},
    {'op': 'check', 'path': '/foo/bar', 'value': 'bar', 'cmp': 'equals'},
    {'op': 'merge', 'path': '/foo', 'value': {'newbar': 'newbarvalue'}},
    {'op': 'check', 'path': '/foo/newbar', 'value': 'newb', 'cmp': 'custom', 'comparator': StartsWithComparator},
    {'op': 'mutate', 'path': '/foo/newbar', 'mut': 'uppercase'},
    {'op': 'mutate', 'path': '/foo/newbar', 'mut': 'custom', 'mutator': RemoveLastMutator},
    {'op': 'mutate', 'path': '/foo/bar', 'mut': ['uppercase', ('custom', RemoveLastMutator)]},
])
doc = {}
result = patch.apply(doc)
print(result)
```

Output:

```text
{'foo': {'bar': 'BARVALU', 'newbar': 'NEWBARVALU'}}
```

### Author

Rangel Reale (rangelspam@gmail.com)
