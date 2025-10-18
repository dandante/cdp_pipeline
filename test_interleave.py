import unittest

import interleave as il

class TestInterleave(unittest.TestCase):

    def test_wrap(self):
        files = ['file1.txt', 'file2.txt']
        func = lambda x: x.upper()
        result = il.wrap(files, func)
        self.assertEqual(result, ['FILE1.TXT', 'FILE2.TXT'])

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2) # pyright: ignore

if __name__ == '__main__':
    unittest.main()
