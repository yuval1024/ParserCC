#!/usr/bin/env python3
import os.path
import unittest

from utils import helpers
from utils.singletonmetaclass import SingletonMetaClass

class ClassA(metaclass=SingletonMetaClass):
    def __init__(self):
        pass


class ClassB(metaclass=SingletonMetaClass):
    def __init__(self):
        pass

class TestSingleton(unittest.TestCase):
    def test_upper(self):
        inst_a_1 = ClassA()
        inst_b_1 = ClassB()
        inst_a_2 = ClassA()
        inst_b_2 = ClassB()

        self.assertEqual(id(inst_a_1), id(inst_a_2))
        self.assertEqual(id(inst_b_1), id(inst_b_2))

        self.assertNotEqual(id(inst_a_1), id(inst_b_1))
        self.assertNotEqual(id(inst_a_1), id(inst_b_2))
        self.assertNotEqual(id(inst_a_2), id(inst_b_1))
        self.assertNotEqual(id(inst_a_2), id(inst_b_2))


class TestProjectRoot(unittest.TestCase):
    def test_project_root(self):
        project_root = helpers.get_project_root_path()
        self.assertIsNotNone(project_root)

    def test_resources_path(self):
        project_root = helpers.get_project_root_path()
        path_apps_json = os.path.join(project_root, "resources", "apps.json")
        self.assertTrue(os.path.isfile(path_apps_json))


if __name__ == '__main__':
    unittest.main()
