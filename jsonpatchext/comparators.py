import re

from jsonpatch import JsonPatchTestFailed


def EqualsComparator(current, compare):
    """Compare if the values are exactly equals."""
    if current != compare:
        msg = '{0} ({1}) is not equal to value {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))


def NotEqualsComparator(current, compare):
    """Compare if the values are not equals."""
    if current == compare:
        msg = '{0} ({1}) is equal to value {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))


def RegExComparator(current, compare):
    """Checks to see if a string matches a regex."""
    if re.compile(compare).search(current) is None:
        msg = '{0} ({1}) does not match the regex {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))


def StartsWithComparator(current, compare):
    """Compare if current starts with compare."""
    if not current.startswith(compare):
        msg = '{0} ({1}) does not starts with value {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))


def EndsWithComparator(current, compare):
    """Compare if current ends with compare."""
    if not current.endswith(compare):
        msg = '{0} ({1}) does not ends with value {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))


def LengthComparator(current, compare):
    """Compare if current len is equals the compare value."""
    if len(current) != compare:
        msg = '{0} ({1}) is not of the expected length {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))


def IsAComparator(current, compare):
    """Test to see if a value is an instance of something."""
    if not isinstance(current, compare):
        msg = '{0} ({1}) is not an instance of {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))


def IsComparator(current, compare):
    """Checks for identity not equality."""
    if not current is compare:
        msg = '{0} ({1}) is not {2} ({3})'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))


def RangeComparator(current, compare):
    """Checks if value is in between 2 ranges (compare must be a 2-value tuple/list)."""
    if current < compare[0] or current > compare[1]:
        msg = '{0} ({1}) is between {2} and {3}'
        raise JsonPatchTestFailed(msg.format(current, type(current), compare[0], compare[1]))


def InComparator(current, compare):
    """Test if a key is in a list or dict."""
    if compare not in current:
        msg = '{0} ({1}) is not in {2} ({3})'
        raise JsonPatchTestFailed(msg.format(compare, type(compare), current, type(current)))
