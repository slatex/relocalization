import unittest

from flexi.gf.magma import MagmaGrammar


class TestGrammar(unittest.TestCase):
    def test_sentences(self):
        grammar = MagmaGrammar('DLTenMagma', 'Eng')

        # pairs (sentence, number of readings)
        sentences = [
            ('There is an integer', 1),
            ('Let $...$ be an even integer', 1),
            ('$...$ is an even integer', 1),
        ]

        for sentence, num_readings in sentences:
            with self.subTest(sentence=sentence):
                readings = grammar.parse(sentence)
                self.assertEqual(len(readings), num_readings)

if __name__ == '__main__':
    unittest.main()