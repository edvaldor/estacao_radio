import unittest
from app.scanner.engine import Scanner
class ScannerTest(unittest.TestCase):
 def test_cycle(self):
  s=Scanner([{'frequency_hz':1},{'frequency_hz':2}]);s.start();self.assertEqual(s.next_channel()['frequency_hz'],1);self.assertEqual(s.next_channel()['frequency_hz'],2)
 def test_empty(self):
  with self.assertRaises(ValueError): Scanner([]).start()
