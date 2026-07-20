import tempfile
import unittest
from app.backend.models import TuneRequest
from app.backend.receiver import Receiver


class ReceiverTest(unittest.TestCase):
    def test_nfm_maps_to_rtl_fm_compatible_fm_mode(self):
        request = TuneRequest(146_520_000, "nfm")
        command = Receiver().command(request)
        self.assertEqual(command[command.index("-M") + 1], "fm")

    def test_demo_can_restart_after_stop(self):
        receiver = Receiver(demo=True)
        request = TuneRequest(118_000_000, "am")
        self.assertFalse(receiver.running)
        receiver.start(request)
        self.assertTrue(receiver.running)
        receiver.stop()
        self.assertFalse(receiver.running)
        receiver.start(request)
        self.assertTrue(receiver.running)

    def test_frequency_restart_stops_active_recording_without_hardware(self):
        with tempfile.TemporaryDirectory() as directory:
            receiver = Receiver(demo=True, recording_dir=directory)
            request = TuneRequest(118_000_000, "am")
            receiver.start(request)
            receiver.start_recording(request.frequency_hz, request.sample_rate)
            self.assertTrue(receiver.recorder.active)
            receiver.start(request)
            self.assertFalse(receiver.recorder.active)
