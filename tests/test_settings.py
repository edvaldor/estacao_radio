import tempfile,unittest
from pathlib import Path
from app.backend.settings import SettingsStore
class StoreTest(unittest.TestCase):
 def test_persists(self):
  with tempfile.TemporaryDirectory() as d:
   defaults={'mode':'Aviacao','frequency_hz':118000000,'modulation':'am','step_hz':25000,'gain':'auto','squelch':0,'volume':80,'audio_device':'default','rtl_serial':None,'demo_mode':False,'scanner_dwell_seconds':5}
   p=Path(d)/'s.json'; s=SettingsStore(p);s.save({'frequency_hz':118025000});self.assertEqual(s.load(defaults)['frequency_hz'],118025000)
 def test_invalid_persisted_values_fall_back_individually(self):
  defaults={'mode':'Aviacao','frequency_hz':118000000,'modulation':'am','step_hz':25000,'gain':'auto','squelch':0,'volume':80,'audio_device':'default','rtl_serial':None,'demo_mode':False,'scanner_dwell_seconds':5}
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.json'; p.write_text('{"step_hz":"25000","frequency_hz":true,"volume":101,"mode":"Livre"}')
   loaded=SettingsStore(p).load(defaults)
  self.assertEqual(loaded['step_hz'],25000); self.assertEqual(loaded['frequency_hz'],118000000)
  self.assertEqual(loaded['volume'],80); self.assertEqual(loaded['mode'],'Livre')
