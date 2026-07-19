import os
from pathlib import Path
import pwd
import tempfile
import unittest

from app.diagnostics.system import touchscreen_devices, user_can_read


class DiagnosticsTest(unittest.TestCase):
    def test_touchscreen_device_uses_event_name_from_sysfs_path(self):
        with tempfile.TemporaryDirectory() as directory:
            name_path = Path(directory) / 'event42' / 'device' / 'name'
            name_path.parent.mkdir(parents=True)
            name_path.write_text('ADS7846 Touchscreen\n')

            devices = touchscreen_devices(str(Path(directory) / 'event*' / 'device' / 'name'))

        self.assertEqual(devices, [('/dev/input/event42', 'ADS7846 Touchscreen', str(name_path))])

    def test_current_user_can_read_owner_readable_file(self):
        with tempfile.NamedTemporaryFile() as temporary:
            os.chmod(temporary.name, 0o600)
            user = pwd.getpwuid(os.getuid()).pw_name
            self.assertTrue(user_can_read(temporary.name, user))
