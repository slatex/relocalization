import unittest
from io import StringIO

from lxml import etree

from flexi.config import TEST_FILE_DIR
from flexi.gf.magma import MagmaGrammar


class TestGrammar(unittest.TestCase):
    def test_basic(self):
        grammar = MagmaGrammar('XLTenMagma', 'Eng')
        masts = grammar.parse_ftml_to_mast(
            etree.parse(
                StringIO(
                    '<p>There is an integer.</p>'
                )
            )
        )
        self.assertEqual(len(masts), 1)
        self.assertEqual(len(masts[0]), 1)
        mast = masts[0][0]
        string = grammar.linearize_mast(mast)
        # some polishing is still needed
        self.assertEqual(string, '<p > there is an integer . </p>')

    def test_ftml_files_parsability(self):
        grammar = MagmaGrammar('XLTenMagma', 'Eng')
        for testfile in ['positive-integer.en.html']:
            with self.subTest(testfile=testfile):
                ftml = etree.parse(
                    TEST_FILE_DIR / 'ftml' / testfile,
                )
                masts = grammar.parse_ftml_to_mast(ftml)
                self.assertGreater(len(masts), 0, f'No MASTs parsed from {testfile}')
