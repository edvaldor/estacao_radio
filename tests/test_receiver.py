import unittest
from app.backend.models import TuneRequest
from app.backend.receiver import Receiver


class ReceiverTest(unittest.TestCase):
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
