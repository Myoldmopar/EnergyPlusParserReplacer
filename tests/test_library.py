from pathlib import Path
import unittest

from parser_replacer.library import Replacement


class TestReplacement(unittest.TestCase):

    def test_construction(self):
        Replacement(Path("hello"), 1, "foo", "bar")
        self.assertTrue(True)
