from __future__ import unicode_literals

import sys
import unittest

import jsonpatch

import jsonpatchext


def ComparatorStartsWith(v1, v2):
    if not v1.startswith(v2):
        msg = '{0} ({1}) doest not starts with {2} ({3})'
        raise jsonpatch.JsonPatchTestFailed(msg.format(v1, type(v1), v2, type(v2)))


class ApplyPatchTestCase(unittest.TestCase):

    def test_check_equals(self):
        obj = {'foo': {'bar': 'baz'}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': 'baz', 'cmp': 'equals'}])
        except jsonpatchext.JsonPatchTestFailed:
            self.fail('test_check_equals() raise JsonPatchTestFailed unexpectedly!')

    def test_check_equals_fail(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': 'foot', 'cmp': 'equals'}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

    def test_check_custom(self):
        obj = {'foo': {'bar': 'baz'}}
        try:
            jsonpatchext.apply_patch(obj, [{'op': 'check', 'path': '/foo/bar', 'value': 'b',
                'cmp': 'custom', 'comparator': ComparatorStartsWith}])
        except jsonpatchext.JsonPatchTestFailed:
            self.fail('test_check_custom() raise JsonPatchTestFailed unexpectedly!')

    def test_check_custom_fail(self):
        obj = {'foo': {'bar': 'baz'}}
        patch_obj = [{'op': 'check', 'path': '/foo/bar', 'value': 'c', 'cmp': 'custom',
            'comparator': ComparatorStartsWith}]
        self.assertRaises(jsonpatch.JsonPatchTestFailed, jsonpatchext.apply_patch, obj, patch_obj)

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
