import re


def UppercaseMutator(current, value):
    """Uppercase the value."""
    return current.upper()


def LowercaseMutator(current, value):
    """Lower the value."""
    return current.lower()


def CastMutator(current, value):
    """Cast value."""
    return value(current)


def RegExMutator(current, value):
    """RegEx replace value. Value must be a tuple (pattern, repl)"""
    return re.sub(value[0], value[1], current)


def SliceMutator(current, value):
    """Returns a slice of the current value. Value must be a tuple (start, stop) or (start, stop, step)"""
    return current[slice(value[0], value[1], value[2] if len(value) > 2 else None)]
