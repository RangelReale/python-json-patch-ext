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
from future.utils import raise_with_traceback

import sys

from deepmerge import merge_or_raise
from deepmerge.exception import InvalidMerge
from jsonpatch import PatchOperation, JsonPatchTestFailed, InvalidJsonPatch, \
    JsonPatchConflict, JsonPatch
from jsonpointer import JsonPointerException

try:
    from collections.abc import MutableMapping, MutableSequence

except ImportError:
    from collections import MutableMapping, MutableSequence
    str = unicode

# Will be parsed by setup.py to determine package metadata
__author__ = 'Rangel Reale <rangelspam@gmail.com>'
__version__ = '1.25'
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

    This modules add 2 more operations: 'check' and 'merge'.

    >>> def StartsWithComparator(v1, v2):
    ...     if v1.startswith(v2):
    ...         msg = '{0} ({1}) does not starts with {2} ({3})'
    ...         raise JsonPatchTestFailed(msg.format(v1, type(v1), v2, type(v2)))

    >>> patch = JsonPatchExt([
    ...     {'op': 'add', 'path': '/foo', 'value': {'bar': 'barvalue'}},
    ...     {'op': 'check', 'path': '/foo/bar', 'value': 'bar', 'cmp': 'equals'},
    ...     {'op': 'merge', 'path': '/foo', 'value': {'newbar': 'newbarvalue'}},
    ...     {'op': 'check', 'path': '/foo/newbar', 'value': 'newb', 'cmp': 'custom', 'comparator': StartsWithComparator},
    ... ])
    >>> doc = {}
    >>> result = patch.apply(doc)
    >>> expected = {'foo': {'bar': 'barvalue', 'newbar': 'newbarvalue'}}
    >>> result == expected
    True
    """
    def __init__(self, patch):
        super(JsonPatchExt, self).__init__(patch)
        self.operations.update({
            'check': CheckOperation,
            'merge': MergeOperation,
        })


class CheckOperation(PatchOperation):
    """Check value by specified location using a comparator."""

    def __init__(self, operation):
        super(CheckOperation, self).__init__(operation)

        self.comparators = {
            'equals': EqualsComparator,
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
            raise InvalidJsonPatch("'path' with '-' can't be applied to 'replace' operation")

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
            if part is not None:
                subobj[part] = merge_or_raise.merge(subobj[part], value)
            else:
                merge_or_raise.merge(subobj, value)
        except InvalidMerge as e:
            raise_with_traceback(InvalidJsonPatch('Invalid merge: {}'.format(str(e))))

        return obj



def EqualsComparator(v1, v2):
    """Compare if the values are exactly equals."""
    if v1 != v2:
        msg = '{0} ({1}) is not equal to tested value {2} ({3})'
        raise JsonPatchTestFailed(msg.format(v1, type(v1), v2, type(v2)))
