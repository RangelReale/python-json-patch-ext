# -*- coding: utf-8 -*-
#
# python-json-patch-ext - An implementation of the JSON Patch format
# https://github.com/RangelReale/python-json-patch-ext
#
# Copyright (c) 2020 Rangel Reale <rangelspam@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

""" Apply JSON-Patches (RFC 6902) with extensions """

from __future__ import unicode_literals

import sys

from deepmerge import Merger
from deepmerge.exception import InvalidMerge
from future.utils import raise_with_traceback
from jsonpatch import PatchOperation, JsonPatchTestFailed, InvalidJsonPatch, \
    JsonPatchConflict, JsonPatch
from jsonpointer import JsonPointerException

from jsonpatchext.comparators import EqualsComparator, NotEqualsComparator, RegExComparator, StartsWithComparator, \
    EndsWithComparator, LengthComparator, IsAComparator, IsComparator, RangeComparator, InComparator
from jsonpatchext.mutators import UppercaseMutator, LowercaseMutator, CastMutator, RegExMutator, SliceMutator, \
    InitMutator

try:
    from collections.abc import MutableMapping, MutableSequence

except ImportError:
    from collections import MutableMapping, MutableSequence
    str = unicode

# Will be parsed by setup.py to determine package metadata
__author__ = 'Rangel Reale <rangelspam@gmail.com>'
__version__ = '1.37'
__website__ = 'https://github.com/RangelReale/python-json-patch-ext'
__license__ = 'Modified BSD License'


# pylint: disable=E0611,W0404
if sys.version_info >= (3, 0):
    basestring = (bytes, str)  # pylint: disable=C0103,W0622


def apply_patch(doc, patch, in_place=False):
    """Apply list of patches to specified json document.

    :param doc: Document object.
    :type doc: dict

    :param patch: JSON patch as list of dicts or raw JSON-encoded string.
    :type patch: list or str

    :param in_place: While :const:`True` patch will modify target document.
                     By default patch will be applied to document copy.
    :type in_place: bool

    :return: Patched document object.
    :rtype: dict
    """

    if isinstance(patch, basestring):
        patch = JsonPatchExt.from_string(patch)
    else:
        patch = JsonPatchExt(patch)
    return patch.apply(doc, in_place)


def make_patch(src, dst):
    """Generates patch by comparing two document objects. Actually is
    a proxy to :meth:`JsonPatch.from_diff` method.

    :param src: Data source document object.
    :type src: dict

    :param dst: Data source document object.
    :type dst: dict
    """

    return JsonPatchExt.from_diff(src, dst)


class JsonPatchExt(JsonPatch):
    """A JSON Patch is a list of Patch Operations.

    This modules add 3 more operations: 'check', 'mutate' and 'merge'.

    >>> def StartsWithComparator(current, compare):
    ...     if not current.startswith(compare):
    ...         msg = '{0} ({1}) does not starts with {2} ({3})'
    ...         raise JsonPatchTestFailed(msg.format(current, type(current), compare, type(compare)))

    >>> def RemoveLastMutator(current, value):
    ...     return current[:-1]

    >>> patch = JsonPatchExt([
    ...     {'op': 'add', 'path': '/foo', 'value': {'bar': 'bar'}},
    ...     {'op': 'check', 'path': '/foo/bar', 'value': 'bar', 'cmp': 'equals'},
    ...     {'op': 'merge', 'path': '/foo', 'value': {'newbar': 'newbarvalue'}},
    ...     {'op': 'check', 'path': '/foo/newbar', 'value': 'newb', 'cmp': 'custom', 'comparator': StartsWithComparator},
    ...     {'op': 'mutate', 'path': '/foo/newbar', 'mut': 'uppercase'},
    ...     {'op': 'mutate', 'path': '/foo/newbar', 'mut': 'custom', 'mutator': RemoveLastMutator},
    ...     {'op': 'mutate', 'path': '/foo/bar', 'mut': ['uppercase', ('custom', RemoveLastMutator)]},
    ... ])
    >>> doc = {}
    >>> result = patch.apply(doc)
    >>> print(result)
    {'foo': {'bar': 'BA', 'newbar': 'NEWBARVALU'}}
    """
    def __init__(self, patch):
        super(JsonPatchExt, self).__init__(patch)
        self.operations.update({
            'check': CheckOperation,
            'mutate': MutateOperation,
            'merge': MergeOperation,
        })

        self.check_operations = {
            'check': CheckOperation,
        }

    def check(self, obj):
        """Checks the object using the patch.

        :param obj: Document object.
        :type obj: Mapping

        :return: whether the check succedded
        :rtype: bool
        """
        for operation in self._check_ops:
            try:
                operation.apply(obj)
            except JsonPatchTestFailed:
                return False

        return True

    @property
    def _check_ops(self):
        return tuple(map(self._get_check_operation, self.patch))

    def _get_check_operation(self, operation):
        if 'op' not in operation:
            raise InvalidJsonPatch("Operation does not contain 'op' member")

        op = operation['op']

        if not isinstance(op, basestring):
            raise InvalidJsonPatch("Operation must be a string")

        if op not in self.check_operations:
            raise InvalidJsonPatch("Unknown operation {0!r}".format(op))

        cls = self.check_operations[op]
        return cls(operation)


class CheckOperation(PatchOperation):
    """Check value by specified location using a comparator."""

    def __init__(self, operation):
        super(CheckOperation, self).__init__(operation)

        self.comparators = {
            'equals': EqualsComparator,
            'notequals': NotEqualsComparator,
            'regex': RegExComparator,
            'startswith': StartsWithComparator,
            'endswith': EndsWithComparator,
            'length': LengthComparator,
            'isa': IsAComparator,
            'is': IsComparator,
            'range': RangeComparator,
            'in': InComparator,
            'custom': None,
        }

    def apply(self, obj):
        try:
            subobj, part = self.pointer.to_last(obj)
            if part is None:
                val = subobj
            else:
                val = self.pointer.walk(subobj, part)
        except JsonPointerException as ex:
            raise JsonPatchTestFailed(str(ex))

        try:
            value = self.operation['value']
        except KeyError as ex:
            raise InvalidJsonPatch(
                "The operation does not contain a 'value' member")

        self._get_comparator()(val, value)

        return obj

    def _get_comparator(self):
        if 'cmp' not in self.operation:
            raise InvalidJsonPatch("Operation does not contain 'cmp' member")

        cmp = self.operation['cmp']

        if not isinstance(cmp, basestring):
            raise InvalidJsonPatch("Comparator must be a string")

        if cmp == 'custom':
            if 'comparator' not in self.operation:
                raise InvalidJsonPatch("Operation does not contain 'comparator' member")
            return self.operation['comparator']

        if cmp not in self.comparators:
            raise InvalidJsonPatch("Unknown comparator {0!r}".format(cmp))

        return self.comparators[cmp]


class MutateOperation(PatchOperation):
    """Check value by specified location using a comparator."""

    def __init__(self, operation):
        super(MutateOperation, self).__init__(operation)

        self.mutators = {
            'uppercase': UppercaseMutator,
            'lowercase': LowercaseMutator,
            'cast': CastMutator,
            'regex': RegExMutator,
            'slice': SliceMutator,
            'init': InitMutator,
            'custom': None,
        }

    def apply(self, obj):
        subobj, part = self.pointer.to_last(obj)

        if part == "-":
            raise InvalidJsonPatch("'path' with '-' can't be applied to 'mutation' operation")

        if isinstance(subobj, MutableSequence):
            if part >= len(subobj) or part < 0:
                raise JsonPatchConflict("can't replace outside of list")

        elif isinstance(subobj, MutableMapping):
            # allow mutating non-existent key
            pass
        else:
            if part is None:
                raise TypeError("invalid document type {0}".format(type(subobj)))
            else:
                raise JsonPatchConflict("unable to fully resolve json pointer {0}, part {1}".format(self.location, part))

        try:
            if part is not None:
                subobj[part] = self._apply_mutators(subobj[part] if part in subobj else None)
            else:
                self._apply_mutators(subobj)
        except Exception as e:
            raise_with_traceback(InvalidJsonPatch('Invalid mutation: {}'.format(str(e))))

        return obj

    def _apply_mutators(self, val):
        if 'mut' not in self.operation:
            raise InvalidJsonPatch("Operation does not contain 'mut' member")

        mut = self.operation['mut']

        if not isinstance(mut, basestring):
            raise InvalidJsonPatch("Mutator must be a string")

        value = self.operation['value'] if 'value' in self.operation else None

        if mut == 'custom':
            if 'mutator' not in self.operation:
                raise InvalidJsonPatch("Operation does not contain 'mutator' member")
            return self.operation['mutator'](val, value)

        if mut not in self.mutators:
            raise InvalidJsonPatch("Unknown mutator {0!r}".format(mut))

        return self.mutators[mut](val, value)


def merge_type_conflict(config, path, base, nxt):
    if len(path) > 0:
        raise InvalidMerge("Type conflict at '/{}': {}, {}".format(
            '/'.join(path), type(base), type(nxt)
        ))
    raise InvalidMerge("Type conflict: {}, {}".format(
        type(base), type(nxt)
    ))


def merge_fallback(config, path, base, nxt):
    if len(path) > 0:
        raise InvalidMerge("Merge fallback at '/{}': {}, {}".format(
            '/'.join(path), type(base), type(nxt)
        ))
    raise InvalidMerge("Merge fallback: {}, {}".format(
        type(base), type(nxt)
    ))


MergeOperationMerger = Merger(
    [
        (list, "append"),
        (dict, "merge")
    ],
    [merge_fallback], [merge_type_conflict]
)


class MergeOperation(PatchOperation):
    """Merges an object property or an array element with a new value, using package deepmerge."""

    def apply(self, obj):
        try:
            value = self.operation["value"]
        except KeyError as ex:
            raise InvalidJsonPatch(
                "The operation does not contain a 'value' member")

        subobj, part = self.pointer.to_last(obj)

        if part == "-":
            raise InvalidJsonPatch("'path' with '-' can't be applied to 'merge' operation")

        if isinstance(subobj, MutableSequence):
            if part >= len(subobj) or part < 0:
                raise JsonPatchConflict("can't replace outside of list")

        elif isinstance(subobj, MutableMapping):
            if part is not None and part not in subobj:
                msg = "can't replace a non-existent object '{0}'".format(part)
                raise JsonPatchConflict(msg)
        else:
            if part is None:
                raise TypeError("invalid document type {0}".format(type(subobj)))
            else:
                raise JsonPatchConflict("unable to fully resolve json pointer {0}, part {1}".format(self.location, part))

        try:
            self.apply_merge(subobj, part, value)
        except InvalidMerge as e:
            raise_with_traceback(InvalidJsonPatch('Invalid merge at "{}": {}'.format(
                self.location, str(e))))

        return obj

    def apply_merge(self, subobj, part, value):
        if part is not None:
            subobj[part] = MergeOperationMerger.merge(subobj[part], value)
        else:
            MergeOperationMerger.merge(subobj, value)
