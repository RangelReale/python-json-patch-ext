from __future__ import unicode_literals

import sys
import unittest

import jsonpatch

import jsonpatchext


def MyComparatorStartsWith(v1, v2):
    if not v1.startswith(v2):
        msg = '{0} ({1}) doest not starts with {2} ({3})'
        raise jsonpatch.JsonPatchTestFailed(msg.format(v1, type(v1), v2, type(v2)))


class ApplyPatchTestCase(unittest.TestCase):

    def test_merge_dict(self):
        obj = {'foo': {'bar': 'baz'}}
        res = jsonpatchext.apply_patch(obj, [{'op': 'merge', 'path': '/foo', 'value': {'corge': 'grault'}}])
        self.assertEqual(res, {'foo': {'bar': 'baz', 'corge': 'grault'}})

    def test_merge_dict_root(self):
        obj = {'foo': {'bar': 'baz'}}
        res = jsonpatchext.apply_patch(obj, [{'op': 'merge', 'path': '', 'value': {'corge': 'grault'}}])
        self.assertEqual(res, {'foo': {'bar': 'baz'}, 'corge': 'grault'})

    def test_merge_list(self):
        obj = {'foo': ['bar', 'baz']}
        res = jsonpatchext.apply_patch(obj, [{'op': 'merge', 'path': '/foo', 'value': ['corge', 'grault']}])
        self.assertEqual(res, {'foo': ['bar', 'baz', 'corge', 'grault']})

    def test_merge_list_to_dict(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'merge', 'path': '/foo', 'value': ['corge', 'grault']}]
        self.assertRaises(jsonpatch.InvalidJsonPatch, jsonpatchext.apply_patch, obj, patch_obj)

    def test_merge_dict_to_list(self):
        obj = {'foo': ['bar', 'baz']}
        patch_obj = [{'op': 'merge', 'path': '/foo', 'value': {'corge': 'grault'}}]
        self.assertRaises(jsonpatch.InvalidJsonPatch, jsonpatchext.apply_patch, obj, patch_obj)

    def test_merge_value_to_dict(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'merge', 'path': '/foo', 'value': 32}]
        self.assertRaises(jsonpatch.InvalidJsonPatch, jsonpatchext.apply_patch, obj, patch_obj)

    def test_merge_dict_to_value(self):
        obj = {'foo': 32}
        patch_obj = [{'op': 'merge', 'path': '/foo', 'value': {'bar': 'baz'}}]
        self.assertRaises(jsonpatch.InvalidJsonPatch, jsonpatchext.apply_patch, obj, patch_obj)

    def test_merge_value_to_list(self):
        obj = {'foo': ['bar', 'baz']}
        patch_obj = [{'op': 'merge', 'path': '/foo', 'value': 32}]
        self.assertRaises(jsonpatch.InvalidJsonPatch, jsonpatchext.apply_patch, obj, patch_obj)

    def test_merge_list_to_value(self):
        obj = {'foo': 32}
        patch_obj = [{'op': 'merge', 'path': '/foo', 'value': ['bar', 'baz']}]
        self.assertRaises(jsonpatch.InvalidJsonPatch, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_equals(self):
        obj = {'foo': {'bar': 'baz'}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': 'baz', 'cmp': 'equals'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_equals() raise JsonPatchTestFailed unexpectedly!')

    def test_check_equals_fail(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': 'foot', 'cmp': 'equals'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_custom(self):
        obj = {'foo': {'bar': 'baz'}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': 'b',
                'cmp': 'custom', 'comparator': MyComparatorStartsWith}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_custom() raise JsonPatchTestFailed unexpectedly!')

    def test_check_custom_fail(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': 'c', 'cmp': 'custom',
            'comparator': MyComparatorStartsWith}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_notequals(self):
        obj = {'foo': {'bar': 'baz'}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': 'bat', 'cmp': 'notequals'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_notequals() raise JsonPatchTestFailed unexpectedly!')

    def test_check_regex(self):
        obj = {'foo': {'bar': 'baz'}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': 'b..', 'cmp': 'regex'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_regex() raise JsonPatchTestFailed unexpectedly!')

    def test_check_regex_fail(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': 'b...', 'cmp': 'regex'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_startswith(self):
        obj = {'foo': {'bar': 'baz'}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': 'b', 'cmp': 'startswith'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_startswith() raise JsonPatchTestFailed unexpectedly!')

    def test_check_startswith_fail(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': 'x', 'cmp': 'startswith'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_endswith(self):
        obj = {'foo': {'bar': 'baz'}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': 'z', 'cmp': 'endswith'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_endswith() raise JsonPatchTestFailed unexpectedly!')

    def test_check_endswith_fail(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': 'x', 'cmp': 'endswith'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_length(self):
        obj = {'foo': ['bar', 'baz']}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo', 'value': 2, 'cmp': 'length'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_length() raise JsonPatchTestFailed unexpectedly!')

    def test_check_length_fail(self):
        obj = {'foo': ['bar', 'baz']}
        patch_obj = [{'op': 'check', 'path': '/foo', 'value': 3, 'cmp': 'length'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_isa(self):
        obj = {'foo': {'bar': 'baz'}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': str, 'cmp': 'isa'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_isa() raise JsonPatchTestFailed unexpectedly!')

    def test_check_isa_fail(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': int, 'cmp': 'isa'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_is(self):
        obj = {'foo': {'bar': None}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': None, 'cmp': 'is'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_is() raise JsonPatchTestFailed unexpectedly!')

    def test_check_is_fail(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': None, 'cmp': 'is'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_range(self):
        obj = {'foo': {'bar': 15}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': (10, 20), 'cmp': 'range'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_range() raise JsonPatchTestFailed unexpectedly!')

    def test_check_range_fail(self):
        obj = {'foo': {'bar': 90}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': (20, 20), 'cmp': 'range'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_in(self):
        obj = {'foo': ['bar', 'baz']}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo', 'value': 'baz', 'cmp': 'in'}])
        except jsonpatch.JsonPatchTestFailed:
            self.fail('test_check_in() raise JsonPatchTestFailed unexpectedly!')

    def test_check_in_fail(self):
        obj = {'foo': ['bar', 'baz']}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': 'foo', 'cmp': 'in'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)


if __name__ == '__main__':
    modules = ['jsonpatchext']


    def get_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(ApplyPatchTestCase))
        return suite


    suite = get_suite()

    for module in modules:
        m = __import__(module, fromlist=[module])
        # suite.addTest(doctest.DocTestSuite(m))

    runner = unittest.TextTestRunner(verbosity=1)

    result = runner.run(suite)

    if not result.wasSuccessful():
        sys.exit(1)
