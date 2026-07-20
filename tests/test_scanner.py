import unittest
from app.scanner.engine import Scanner
class ScannerTest(unittest.TestCase):
 def test_cycle(self):
  s=Scanner([{'frequency_hz':1},{'frequency_hz':2}]);s.start();self.assertEqual(s.next_channel()['frequency_hz'],1);self.assertEqual(s.next_channel()['frequency_hz'],2)
 def test_empty(self):
  with self.assertRaises(ValueError): Scanner([]).start()
 def test_dwell_prevents_early_channel_change(self):
  s=Scanner([{'frequency_hz':1},{'frequency_hz':2}], dwell_seconds=5);s.start(now=10)
  self.assertEqual(s.tick(now=10)['frequency_hz'],1)
  self.assertIsNone(s.tick(now=14.9))
  self.assertEqual(s.tick(now=15)['frequency_hz'],2)
