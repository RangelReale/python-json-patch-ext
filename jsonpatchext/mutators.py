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


def InitMutator(current, value):
    """Initialize the value if it is None"""
    if current is None:
        return value
    return current


def InitItemMutator(*item):
    """Initialize an item in a dict/list if it does not exists or is None. If more than one item, create the full hierarchy"""
    def m(current, value):
        # plist, plast = item[:len(item)-1], item[len(item)-1]
        plist, plast = item[:-1], item[-1]
        cur = current
        for i in plist:
            if i not in cur or cur[i] is None:
                cur[i] = {}
            cur = cur[i]
        if plast not in cur or cur[plast] is None:
            cur[plast] = value
        return current
    return m
