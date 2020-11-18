from jsonpatchext import JsonPatchExt, JsonPatchTestFailed

def StartsWithComparator(current, compare):
    if not current.startswith(compare):
        msg = '{0} ({1}) does not starts with {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))

def RemoveLastMutator(current, value):
    return current[:-1]

patch = JsonPatchExt([
    {'op': 'add', 'path': '/foo', 'value': {'bar': 'bar'}},
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

checkpatch = JsonPatchExt([
    {'op': 'check', 'path': '/foo/bar', 'value': 'BA', 'cmp': 'equals'},
    {'op': 'check', 'path': '/foo/newbar', 'value': 'NEWB', 'cmp': 'custom', 'comparator': StartsWithComparator},
])

result = checkpatch.check(result)
print(result)
