#!/usr/bin/env python3
"""Read macOS CoreMIDI sources without third-party packages or MIDI output.

Examples:
  python3 tools/capture_midi.py --list
  python3 tools/capture_midi.py --source 'MPC Key 37' --seconds 45 --label standalone
"""
import argparse
import ctypes as C
import json
import platform
import queue
import sys
import time


class Decoder:
    """Streaming MIDI 1 decoder; handles running status and interleaved clock."""
    def __init__(self):
        self.status = None
        self.data = []
        self.sysex = None

    def feed(self, data):
        for byte in data:
            if byte >= 0xF8:
                continue
            if byte == 0xF0:
                self.status, self.data, self.sysex = None, [], [byte]
            elif byte == 0xF7:
                if self.sysex is not None:
                    yield {"type": "sysex", "bytes": self.sysex + [byte]}
                self.sysex = None
            elif byte & 0x80:
                self.sysex = None
                self.status = byte if byte < 0xF0 else None
                self.data = []
            elif self.sysex is not None:
                self.sysex.append(byte)
            elif self.status is not None:
                self.data.append(byte)
                kind = self.status >> 4
                size = 1 if kind in (0xC, 0xD) else 2
                if len(self.data) == size:
                    values = self.data
                    names = {8: "note_off", 9: "note", 10: "poly_pressure",
                             11: "cc", 12: "program", 13: "pressure", 14: "pitchbend"}
                    event = {"type": names[kind], "channel": (self.status & 15) + 1,
                             "bytes": [self.status] + values}
                    if kind == 14:
                        event["value"] = values[0] | values[1] << 7
                    elif size == 2:
                        event.update(identifier=values[0], value=values[1])
                    else:
                        event["value"] = values[0]
                    yield event
                    self.data = []


class CoreMIDI:
    def __init__(self):
        if platform.system() != "Darwin":
            raise RuntimeError("This capture utility requires macOS CoreMIDI.")
        self.midi = C.CDLL("/System/Library/Frameworks/CoreMIDI.framework/CoreMIDI")
        self.cf = C.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        self.callback_type = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p, C.c_void_p)
        self._configure()

    def _configure(self):
        signatures = {
            "MIDIGetNumberOfSources": ([], C.c_size_t),
            "MIDIGetSource": ([C.c_size_t], C.c_uint32),
            "MIDIObjectGetStringProperty": ([C.c_uint32, C.c_void_p, C.POINTER(C.c_void_p)], C.c_int32),
            "MIDIClientCreate": ([C.c_void_p, C.c_void_p, C.c_void_p, C.POINTER(C.c_uint32)], C.c_int32),
            "MIDIInputPortCreate": ([C.c_uint32, C.c_void_p, self.callback_type, C.c_void_p, C.POINTER(C.c_uint32)], C.c_int32),
            "MIDIPortConnectSource": ([C.c_uint32, C.c_uint32, C.c_void_p], C.c_int32),
            "MIDIPortDispose": ([C.c_uint32], C.c_int32),
            "MIDIClientDispose": ([C.c_uint32], C.c_int32),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.midi, name)
            fn.argtypes, fn.restype = args, result
        self.cf.CFStringCreateWithCString.argtypes = [C.c_void_p, C.c_char_p, C.c_uint32]
        self.cf.CFStringCreateWithCString.restype = C.c_void_p
        self.cf.CFStringGetCString.argtypes = [C.c_void_p, C.c_char_p, C.c_long, C.c_uint32]
        self.cf.CFStringGetCString.restype = C.c_bool
        self.cf.CFRelease.argtypes = [C.c_void_p]

    def string(self, value):
        return self.cf.CFStringCreateWithCString(None, value.encode(), 0x08000100)

    def sources(self):
        key = C.c_void_p.in_dll(self.midi, "kMIDIPropertyDisplayName")
        result = []
        for i in range(self.midi.MIDIGetNumberOfSources()):
            endpoint = self.midi.MIDIGetSource(i)
            value = C.c_void_p()
            name = "Source {}".format(i)
            if not self.midi.MIDIObjectGetStringProperty(endpoint, key, C.byref(value)):
                buf = C.create_string_buffer(1024)
                self.cf.CFStringGetCString(value, buf, len(buf), 0x08000100)
                name = buf.value.decode("utf-8", errors="replace")
                self.cf.CFRelease(value)
            result.append({"index": i, "endpoint": endpoint, "name": name})
        return result

    def capture(self, sources, seconds):
        messages = queue.Queue()

        @self.callback_type
        def receive(packet_list, _, source_ref):
            # MIDIPacketList uses 4-byte packing on macOS (including arm64).
            count = C.c_uint32.from_address(packet_list).value
            pointer = packet_list + 4
            for _ in range(count):
                length = C.c_uint16.from_address(pointer + 8).value
                messages.put((int(source_ref), time.time(), C.string_at(pointer + 10, length)))
                pointer += (10 + length + 3) & ~3

        client, port = C.c_uint32(), C.c_uint32()
        label = self.string("MPC Key 37 Read-Only Capture")
        try:
            self.check(self.midi.MIDIClientCreate(label, None, None, C.byref(client)))
            self.check(self.midi.MIDIInputPortCreate(client, label, receive, None, C.byref(port)))
            for source in sources:
                self.check(self.midi.MIDIPortConnectSource(port, source["endpoint"], source["endpoint"]))
            names = {s["endpoint"]: s["name"] for s in sources}
            decoders = {s["endpoint"]: Decoder() for s in sources}
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                try:
                    endpoint, timestamp, data = messages.get(timeout=min(0.2, max(0.001, end-time.monotonic())))
                except queue.Empty:
                    continue
                for event in decoders[endpoint].feed(data):
                    yield dict(event, source=names[endpoint], timestamp=timestamp)
        finally:
            if port.value:
                self.midi.MIDIPortDispose(port)
            if client.value:
                self.midi.MIDIClientDispose(client)
            self.cf.CFRelease(label)

    @staticmethod
    def check(status):
        if status:
            raise RuntimeError("CoreMIDI returned OSStatus {}".format(status))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--source", help="Case-insensitive source name substring")
    parser.add_argument("--seconds", type=float, default=45)
    parser.add_argument("--label", default="unlabeled")
    parser.add_argument("--output", help="Optional new JSONL capture file (never overwritten)")
    args = parser.parse_args()
    midi = CoreMIDI()
    sources = midi.sources()
    if args.list:
        print(json.dumps(sources, indent=2))
        return
    if not args.source:
        parser.error("Choose --source from --list; capture never opens every source implicitly.")
    selected = [s for s in sources if args.source.lower() in s["name"].lower()]
    if not selected:
        parser.error("No matching MIDI source. Connect/power the MPC, then run --list again.")
    if not 0 < args.seconds <= 3600:
        parser.error("--seconds must be between 0 and 3600")
    output = open(args.output, "x") if args.output else None
    print("Listening: " + ", ".join(s["name"] for s in selected), file=sys.stderr)
    try:
        for event in midi.capture(selected, args.seconds):
            line = json.dumps(dict(event, label=args.label))
            print(line, flush=True)
            if output:
                output.write(line + "\n")
                output.flush()
    except KeyboardInterrupt:
        pass
    finally:
        if output:
            output.close()


if __name__ == "__main__":
    main()
