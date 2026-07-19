import tempfile,unittest
from pathlib import Path
from app.backend.settings import SettingsStore
class StoreTest(unittest.TestCase):
 def test_persists(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.json'; s=SettingsStore(p);s.save({'frequency_hz':123});self.assertEqual(s.load({'mode':'x'}),{'mode':'x','frequency_hz':123})
