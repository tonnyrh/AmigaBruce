"""Protocol regressions for the monitor failures seen during reference capture."""
from collections import deque
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from vice_binary import Vice


class FakeVice(Vice):
    def __init__(self, responses=(), data=b"", queued=()):
        self.responses=deque(responses)
        self.data=data
        self.events=[]
        self.queued=list(queued)
        self.commands=[]

    def command(self, kind, body=b""):
        self.commands.append((kind,body))
        self.events.extend(self.queued)
        self.queued=[]
        return self.data

    def response(self):
        if not self.responses:
            raise EOFError("No more monitor events")
        kind,body=self.responses.popleft()
        return kind,0,0xffffffff,body


class MonitorTests(unittest.TestCase):
    def test_stale_stop_does_not_finish_new_run(self):
        v=FakeVice(responses=[(0x63,b"\xce\x1b"),(0x62,b"\xce\x1b")],
                   queued=[(0x62,b"\x00\x00")])
        self.assertEqual(v.run_stopped(expected_pc=0x1bce),0x1bce)
        self.assertFalse(v.responses)

    def test_stop_without_resume_is_rejected(self):
        v=FakeVice(responses=[(0x62,b"\xce\x1b")])
        with self.assertRaises(EOFError):v.run_stopped()

    def test_wrong_boundary_and_cpu_jam_are_rejected(self):
        v=FakeVice(responses=[(0x63,b"\0\0"),(0x62,b"\x32\x1c")])
        with self.assertRaisesRegex(RuntimeError,"Wrong stop"):
            v.run_stopped(expected_pc=0x1bce)
        with self.assertRaisesRegex(RuntimeError,"jammed"):
            FakeVice(responses=[(0x61,b"")]).run_stopped()

    def test_register_and_clock_decoding(self):
        v=FakeVice(data=bytes.fromhex("02000303ce1b03350a01"))
        self.assertEqual(v.registers(),{3:0x1bce,0x35:266})
        v.data=bytes.fromhex("010000002f08000303cc1b030001000301ff00030240000304fd00030520000335ffff0336fffffc4c125c0000000004f01120ff")
        self.assertEqual(v.history_clock(),(0x1bcc,0x5c124cfc))

    def test_step_must_leave_current_breakpoint(self):
        v=FakeVice()
        v.run_stopped=lambda *args,**kwargs:0x1bce
        v.registers=lambda:{3:0x1bce}
        with self.assertRaisesRegex(RuntimeError,"did not advance"):
            v.next_hit(12,0x1bce)
        self.assertEqual(v.commands[0],(0x15,struct.pack("<IB",12,False)))

    def test_joystick_uses_active_low_value_and_zero_based_port(self):
        v=FakeVice()
        v.joystick(0xf7)
        self.assertEqual(v.commands,[(0xa2,b"\0\0\xf7\0")])


if __name__=="__main__":unittest.main()
