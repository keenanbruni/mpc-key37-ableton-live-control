"""Validated, human-numbered MIDI configuration; usable outside Live."""
import json
from pathlib import Path

BANK_A = ("previous_device", "next_device", "previous_bank", "next_bank",
          "device_half", "device_lock", "device_enable", "device_mode",
          "previous_track", "next_track", "play", "stop", "session_record",
          "arrangement_record", "loop", "metronome")
BANK_D = tuple("track_{}".format(i + 1) for i in range(8)) + (
    "mute", "solo", "arm", "stop_track", "volume_mode", "pan_mode", "send_mode", "mixer_half")
BANK_E = ("session_left", "session_right", "session_up", "session_down",
          "mixer_left", "mixer_right", "scenes_previous", "scenes_next",
          "continue", "tap_tempo", "undo", "redo", "duplicate", "quantize",
          "stop_all", "status")
ACTIONS = BANK_A + tuple("clip_{}".format(i + 1) for i in range(16)) + tuple(
    "scene_{}".format(i + 1) for i in range(16)) + BANK_D + BANK_E
ENCODINGS = ("absolute", "relative_two_complement", "relative_binary_offset", "relative_signed_bit")


def validate(profile):
    if profile.get("version") != 1:
        raise ValueError("Profile version must be 1")
    if type(profile.get("enabled")) is not bool or type(profile.get("verified")) is not bool:
        raise ValueError("enabled and verified must be true or false")
    performance = profile.get("performance_channel")
    if type(performance) is not int or not 1 <= performance <= 16:
        raise ValueError("performance_channel must be 1–16")
    knobs = profile.get("knobs", [])
    buttons = profile.get("buttons", {})
    if len(knobs) != 4 or not isinstance(buttons, dict):
        raise ValueError("Supply four knobs and a buttons object")
    if set(buttons) - set(ACTIONS):
        raise ValueError("Unknown button actions: " + str(set(buttons) - set(ACTIONS)))
    seen = set()
    for name, binding in list(zip(("Q1", "Q2", "Q3", "Q4"), knobs)) + list(buttons.items()):
        if binding is None:
            continue
        kind, channel, identifier = (binding.get(k) for k in ("type", "channel", "identifier"))
        if kind not in (("cc", "pitchbend") if name in ("Q1", "Q2", "Q3", "Q4") else ("note", "cc")):
            raise ValueError("Invalid message type for " + name)
        if type(channel) is not int or not 1 <= channel <= 16:
            raise ValueError("MIDI channels must be 1–16: " + name)
        if channel == performance:
            raise ValueError("Control and performance channels must differ: " + name)
        if type(identifier) is not int or not 0 <= identifier <= 127:
            raise ValueError("MIDI identifiers must be 0–127: " + name)
        if kind == "pitchbend" and identifier != 0:
            raise ValueError("Pitchbend uses identifier 0")
        key = kind, channel, identifier
        if key in seen:
            raise ValueError("Duplicate MIDI binding: " + str(key))
        seen.add(key)
        if name in ("Q1", "Q2", "Q3", "Q4"):
            encoding = binding.get("encoding")
            if encoding not in ENCODINGS or (kind == "pitchbend" and encoding != "absolute"):
                raise ValueError("Invalid knob encoding: " + name)
    router = profile.get("pad_router")
    physical = list(profile.get("physical_buttons", {}).items())
    if set(profile.get("physical_buttons", {})) - set(ACTIONS):
        raise ValueError("Unknown physical button action")
    if router:
        notes = router.get("notes", [])
        if len(notes) != 16 or len(set(notes)) != 16:
            raise ValueError("pad_router requires 16 unique notes in physical pad order")
        physical += [("pad_{}".format(i), {"type": "note", "channel": router.get("channel"),
                                          "identifier": note}) for i, note in enumerate(notes)]
        selectors = router.get("selectors", {})
        if set(selectors) != set("ABCD"):
            raise ValueError("pad_router requires selectors A–D")
        physical += list(selectors.items())
    for name, binding in physical:
        kind, channel, identifier = (binding.get(k) for k in ("type", "channel", "identifier"))
        if kind not in ("note", "cc") or type(channel) is not int or not 1 <= channel <= 16:
            raise ValueError("Invalid physical binding: " + name)
        if channel == performance:
            raise ValueError("Physical controls overlap performance channel: " + name)
        if type(identifier) is not int or not 0 <= identifier <= 127:
            raise ValueError("Invalid physical identifier: " + name)
        key = kind, channel, identifier
        if key in seen:
            raise ValueError("Duplicate MIDI binding: " + str(key))
        seen.add(key)
    return profile


def load(path=None):
    path = Path(path) if path else Path(__file__).with_name("midi_profile.json")
    with path.open(encoding="utf-8") as stream:
        return validate(json.load(stream))


def four_parameters(parameters, half):
    """Keep the official eight-slot order, including unavailable slots."""
    values = list(parameters)[half * 4:half * 4 + 4]
    return values + [None] * (4 - len(values))


def bounded_offset(current, delta, length, width):
    return max(0, min(current + delta, max(0, length - width)))
