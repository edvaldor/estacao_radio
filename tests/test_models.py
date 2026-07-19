import unittest
from app.backend.models import TuneRequest, validate_frequency
class ModelsTest(unittest.TestCase):
 def test_valid_aviation(self): self.assertEqual(validate_frequency(118000000,'am'),118000000)
 def test_rejects_wfm_outside_band(self):
  with self.assertRaises(ValueError): validate_frequency(118000000,'wfm')
 def test_rejects_invalid_squelch(self):
  with self.assertRaises(ValueError): TuneRequest(118000000,'am',squelch=101)
