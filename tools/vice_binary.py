"""VICE 3.10 inspection client; localhost only, API version 2.

Protocol: https://vice-emu.sourceforge.io/vice_13.html
Use only against the dedicated process started for this project.
Stepping waits for a fresh RESUMED -> STOPPED event pair. A breakpoint on the
current PC must be disabled while stepping past it, or VICE may re-hit it.
"""
import argparse
from pathlib import Path
import socket
import struct


class Vice:
    def __init__(self, port=6511):
        self.socket = socket.create_connection(("127.0.0.1", port), 5)
        self.socket.settimeout(15)
        self.sequence = 0
        self.events = []

    def read(self, count):
        data = bytearray()
        while len(data) < count:
            part = self.socket.recv(count - len(data))
            if not part:
                raise EOFError("VICE disconnected")
            data.extend(part)
        return bytes(data)

    def response(self):
        header = self.read(12)
        stx, version, size, kind, error, request = struct.unpack("<BBIBBI", header)
        if stx != 2 or size > 8 * 1024 * 1024:
            raise ValueError("Invalid VICE response header")
        return kind, error, request, self.read(size)

    def command(self, kind, body=b""):
        self.sequence += 1
        request = self.sequence
        self.socket.sendall(struct.pack("<BBIIB", 2, 2, len(body), request, kind) + body)
        while True:
            response, error, rid, data = self.response()
            if rid == request:
                if error:
                    raise RuntimeError(f"VICE error {error:02x} for command {kind:02x}")
                return data
            self.events.append((response, data))

    def memory(self, start, end, bank=0):
        return self.command(1, struct.pack("<BHHBH", 0, start, end, 0, bank))[2:]

    def snapshot(self, path):
        path = str(Path(path).resolve()).encode("utf-8")
        self.command(0x41, bytes([0, 0, len(path)]) + path)

    def restore(self, path):
        path = str(Path(path).resolve()).encode("utf-8")
        if len(path) > 255:
            raise ValueError("Snapshot path exceeds protocol limit")
        return int.from_bytes(self.command(0x42, bytes([len(path)]) + path), "little")

    def registers(self):
        data = self.command(0x31, b"\0")
        count = int.from_bytes(data[:2], "little")
        offset, values = 2, {}
        for _ in range(count):
            size = data[offset]
            values[data[offset+1]] = int.from_bytes(data[offset+2:offset+size+1], "little")
            offset += size + 1
        return values

    def checkpoint(self, address):
        data = self.command(0x12, struct.pack("<HHBBBBB", address, address, 1, 1, 4, 0, 0))
        return int.from_bytes(data[:4], "little")

    def toggle(self, checkpoint, enabled):
        self.command(0x15, struct.pack("<IB", checkpoint, bool(enabled)))

    def run_stopped(self, kind=0xaa, body=b"", expected_pc=None):
        self.events.clear()
        self.command(kind, body)
        pending, self.events = self.events, []
        resumed = False
        for _ in range(100):
            if pending:
                response, data = pending.pop(0)
            else:
                response, error, _, data = self.response()
                if error:
                    raise RuntimeError(f"VICE asynchronous error {error:02x}")
            if response == 0x61:
                raise RuntimeError("C64 CPU jammed")
            if response == 0x63:
                resumed = True
            if response == 0x62 and resumed:
                pc = int.from_bytes(data[:2], "little")
                if expected_pc is not None and pc != expected_pc:
                    raise RuntimeError(f"Wrong stop: ${pc:04X}, expected ${expected_pc:04X}")
                return pc
        raise RuntimeError("No fresh RESUMED -> STOPPED pair")

    def next_hit(self, checkpoint, address):
        self.toggle(checkpoint, False)
        self.run_stopped(0x71, struct.pack("<BH", 0, 1))
        if self.registers()[3] == address:
            raise RuntimeError("Instruction did not advance past breakpoint")
        self.toggle(checkpoint, True)
        self.run_stopped(expected_pc=address)
        if self.registers()[3] != address:
            raise RuntimeError("Register PC disagrees with STOPPED event")

    def resource_int(self, name, value):
        name = name.encode("ascii")
        self.command(0x52, bytes([1, len(name)]) + name + b"\4" + struct.pack("<I", value))

    def joystick(self, active_low, port=0):
        # Requires JoyPort1Device=37 (IO Simulation); port numbers are zero-based.
        self.command(0xa2, struct.pack("<HH", port, active_low))

    def history_clock(self):
        data = self.command(0x86, b"\0" + struct.pack("<I", 1))
        if int.from_bytes(data[:4], "little") != 1:
            raise RuntimeError("CPU history unavailable")
        size = data[4]
        count = int.from_bytes(data[5:7], "little")
        offset = 7
        registers = {}
        for _ in range(count):
            length = data[offset]
            registers[data[offset+1]] = int.from_bytes(data[offset+2:offset+length+1], "little")
            offset += length + 1
        if offset + 8 > 5 + size:
            raise RuntimeError("Invalid CPU history row")
        return registers[3], int.from_bytes(data[offset:offset+8], "little")

    def image(self, path):
        from PIL import Image
        data = self.command(0x84, b"\x01\x00")
        fields, width, height, x, y, innerw, innerh, bits, size = struct.unpack("<I6HBI", data[:21])
        palette = self.command(0x91, b"\x01")
        colors = []
        offset = 2
        for _ in range(int.from_bytes(palette[:2], "little")):
            length = palette[offset]
            colors.extend(palette[offset + 1:offset + 4])
            offset += length + 1
        pixels = data[21:21+size]
        # VICE 3.10's response length omits four trailing display bytes.
        # Preserve the full geometry and pad only that final border tail.
        if len(pixels) not in (width * height, width * height - 4):
            raise ValueError("Unexpected VICE display payload length")
        image = Image.frombytes("P", (width, height), pixels.ljust(width * height, b"\0"))
        image.putpalette(colors + [0] * (768 - len(colors)))
        image.convert("RGB").save(path)
        return width, height, (x, y, innerw, innerh)

    def close(self, resume=True):
        try:
            if resume:
                self.command(0xaa)
        finally:
            self.socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--memory", type=Path, help="Save a 64K CPU-visible memory read")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--port", type=int, default=6511)
    args = parser.parse_args()
    if not (args.image or args.memory or args.snapshot):
        parser.error("Choose --image, --memory or --snapshot")
    vice = Vice(args.port)
    try:
        if args.image:
            print("Display geometry:", vice.image(args.image))
        if args.memory:
            args.memory.write_bytes(vice.memory(0,65535))
        if args.snapshot:
            vice.snapshot(args.snapshot)
    finally:
        vice.close()
