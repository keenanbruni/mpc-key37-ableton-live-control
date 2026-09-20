"""Input-only controls. Never send the G2/Force display or lighting protocol."""
import Live
from ableton.v2.control_surface import MIDI_CC_TYPE, MIDI_NOTE_TYPE, MIDI_PB_TYPE
from ableton.v2.control_surface.elements import ButtonElement, EncoderElement


class InputButton(ButtonElement):
    def __init__(self, *args, **kwargs):
        self._pressed = False
        super(InputButton, self).__init__(*args, **kwargs)

    def receive_value(self, value):
        # Poly pressure is a separate message type. Multiple positive CC values
        # from one held switch must not re-trigger a command.
        pressed = value > 0
        if pressed != self._pressed:
            self._pressed = pressed
            super(InputButton, self).receive_value(127 if pressed else 0)

    def release(self):
        self.receive_value(0)

    def send_value(self, *args, **kwargs):
        pass


def button(name, binding, skin):
    return InputButton(True, MIDI_NOTE_TYPE if binding["type"] == "note" else MIDI_CC_TYPE,
                       binding["channel"] - 1, binding["identifier"], name=name,
                       skin=skin, is_feedback_enabled=False)


def encoder(name, binding):
    modes = Live.MidiMap.MapMode
    mode = {"absolute": modes.absolute,
            "relative_two_complement": modes.relative_smooth_two_compliment,
            "relative_binary_offset": modes.relative_smooth_binary_offset,
            "relative_signed_bit": modes.relative_smooth_signed_bit}[binding["encoding"]]
    result = EncoderElement(MIDI_PB_TYPE if binding["type"] == "pitchbend" else MIDI_CC_TYPE,
                            binding["channel"] - 1, binding["identifier"], mode,
                            name=name, is_feedback_enabled=False)
    result.set_needs_takeover(binding["encoding"] == "absolute")
    return result
