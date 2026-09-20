"""Hardware adapter; musical behavior is delegated to Live's MPC components."""
import time
import logging
import traceback
from functools import partial

import Live

from ableton.v2.base import liveobj_valid
from ableton.v2.control_surface import (
    BankingInfo, ControlSurface, DeviceDecoratorFactory, Layer, ParameterInfo,
    ParameterProvider, Skin,
)
from ableton.v2.control_surface.components import (
    DeviceParameterComponent, RightAlignTracksTrackAssigner, SessionRingComponent,
    UndoRedoComponent,
)
from ableton.v2.control_surface.control import ControlList, MappedSensitivitySettingControl
from ableton.v2.control_surface.default_bank_definitions import BANK_DEFINITIONS
from ableton.v2.control_surface.elements import ButtonMatrixElement

from Akai_Force_MPC.device import DeviceComponent
from Akai_Force_MPC.device_navigation import ScrollingDeviceNavigationComponent
from Akai_Force_MPC.channel_strip import ChannelStripComponent
from Akai_Force_MPC.mixer import MixerComponent
from Akai_Force_MPC.session import SessionComponent
from Akai_Force_MPC.scene_list import SceneListComponent
from Akai_Force_MPC.transport import MPCTransportComponent
from Akai_Force_MPC.session_recording import SessionRecordingComponent
from Akai_Force_MPC.clip_actions import ClipActionsComponent
from Akai_Force_MPC.skin import MPCColors

from . import elements
from .profile import load, four_parameters, bounded_offset
from .routing import PadRouter


class FourParameterComponent(DeviceParameterComponent):
    controls = ControlList(MappedSensitivitySettingControl, 4)


class FourParameterProvider(ParameterProvider):
    def __init__(self):
        super(FourParameterProvider, self).__init__()
        self._infos = [None] * 4

    @property
    def parameters(self):
        return self._infos

    def set_parameters(self, infos):
        self._infos = infos
        self.notify_parameters()


class MPCKey37(ControlSurface):
    """No product impersonation, ping/pong, display SysEx, or LED output."""
    def __init__(self, *args, **kwargs):
        super(MPCKey37, self).__init__(*args, **kwargs)
        self._ready = False
        self._buttons = {}
        self._encoders = []
        self._callbacks = []
        self._raw_buttons = []
        self._router = PadRouter()
        self._mode = "device"
        self._device_half = self._mixer_half = self._send_index = 0
        self._device_locked = False
        self._mapping_signature = None
        self._last_status = None
        self._runtime_failed = False
        try:
            self._profile = load()
            if not self._profile["enabled"]:
                self.show_message("MPC Key 37: disabled in midi_profile.json")
                return
            with self.component_guard():
                self._create_elements()
                self._create_components()
                self._bind_commands()
                self._bind_hardware()
                self._ready = True
                self._refresh_parameters()
            self.log_message("MPC_Key_37 initialized using bundled Akai_Force_MPC components")
            self.show_message("MPC Key 37 ready" + (" — MIDI profile UNVERIFIED" if not self._profile["verified"] else ""))
        except Exception:
            self.log_message("MPC_Key_37 initialization failed:\n" + traceback.format_exc())
            # Release anything created before the failure; a broken adapter
            # must not leave partially functioning recording commands active.
            for component in self.root_components:
                component.set_enabled(False)
            self._ready = False
            self.show_message("MPC Key 37 could not load. See Live Log.txt and README.")

    def _send_midi(self, *args, **kwargs):
        return False

    def log_message(self, message):
        logging.getLogger(__name__).info(message)

    def _create_elements(self):
        skin = Skin(MPCColors)
        for action, binding in self._profile["buttons"].items():
            if binding is not None:
                self._buttons[action] = elements.button(action, binding, skin)
        self._encoders = [elements.encoder("Q_Link_{}".format(i + 1), binding)
                          if binding else None for i, binding in enumerate(self._profile["knobs"])]

    def _layer(self, **bindings):
        return Layer(**{control: self._buttons[action] for control, action in bindings.items()
                        if action in self._buttons})

    def _matrix(self, actions, width, name):
        controls = [self._buttons.get(action) for action in actions]
        return ButtonMatrixElement(rows=[controls[i:i + width] for i in range(0, len(controls), width)], name=name)

    def _create_components(self):
        self._device = DeviceComponent(
            device_decorator_factory=DeviceDecoratorFactory(),
            device_bank_registry=self._device_bank_registry,
            banking_info=BankingInfo(BANK_DEFINITIONS), toggle_lock=self.toggle_lock,
            name="Device", layer=self._layer(prev_bank_button="previous_bank",
                next_bank_button="next_bank"))
        self._navigation = ScrollingDeviceNavigationComponent(
            device_component=self._device, name="Device_Navigation")
        self._parameter_provider = self.register_disconnectable(FourParameterProvider())
        self._parameter_component = FourParameterComponent(
            parameter_provider=self._parameter_provider, name="Four_Q_Links")
        self._parameter_component.set_parameter_controls(self._encoders)
        self.register_slot(self._device, self._device_parameters_changed, "parameters")

        self._session_ring = SessionRingComponent(num_tracks=4, num_scenes=4, name="Clip_Window")
        self._session = SessionComponent(session_ring=self._session_ring, name="Session")
        # Live 12.4.6's bundled session component accepts native MIDI matrix
        # elements, but does not react when the same pads are routed through
        # our shared-page adapter.  The adapter dispatches to ClipSlot.fire()
        # below, which is the same Live launch operation.
        self._scenes = SceneListComponent(session_ring=self._session_ring, num_scenes=16, name="Scenes")
        self._mixer_ring = SessionRingComponent(num_tracks=8, num_scenes=0,
            set_session_highlight=lambda *a: None,
            # Page D is a track mixer.  Keeping returns and the master out of
            # this ring means an eight-track window always refers to the
            # project's visible tracks, rather than an unexpected mixture of
            # tracks, return channels, and master.
            tracks_to_use=lambda: tuple(self.song.visible_tracks),
            name="Mixer_Window")
        self._mixer = MixerComponent(tracks_provider=self._mixer_ring,
            track_assigner=RightAlignTracksTrackAssigner(song=self.song, include_master_track=False),
            channel_strip_component_type=ChannelStripComponent, name="Mixer")
        # Routed Page D pads are virtual controls, so select directly rather
        # than relying on the bundled mixer's native MIDI button layer.
        self._transport = MPCTransportComponent(name="Transport", layer=self._layer(
            play_button="play", stop_button="stop"))
        # The bundled MPC transport inherits these as setter-managed toggles,
        # rather than declaring them as Layer controls.
        self._transport.set_record_button(self._buttons.get("arrangement_record"))
        self._transport.set_loop_button(self._buttons.get("loop"))
        self._transport.set_metronome_button(self._buttons.get("metronome"))
        self._recording = SessionRecordingComponent(name="Session_Recording")
        self._undo = UndoRedoComponent(name="Undo_Redo")
        self._clip_actions = ClipActionsComponent(name="Clip_Actions")

    def _listen(self, action, callback):
        control = self._buttons.get(action)
        if control is not None:
            def on_value(value):
                if value and self._ready:
                    with self.component_guard():
                        callback()
            control.add_value_listener(on_value)
            self._callbacks.append((control, on_value))

    def _raw_listener(self, name, binding, callback):
        control = elements.button(name, binding, Skin(MPCColors))
        def on_value(value):
            if self._ready:
                with self.component_guard():
                    callback(value)
        control.add_value_listener(on_value)
        self._raw_buttons.append(control)
        self._callbacks.append((control, on_value))

    def _dispatch_pad_events(self, events):
        for action, value in events:
            control = self._buttons.get(action)
            if control:
                control.receive_value(value)

    def _select_page(self, page, value):
        if value:
            self._dispatch_pad_events(self._router.select(page, time.monotonic()))
            self._show_status()

    def _bind_hardware(self):
        router = self._profile.get("pad_router")
        if router:
            for i, note in enumerate(router["notes"]):
                binding = dict(type="note", channel=router["channel"], identifier=note)
                self._raw_listener("Physical_Pad_{}".format(i + 1), binding,
                    lambda value, i=i: self._dispatch_pad_events(self._router.receive(i, value)))
            for page, binding in router["selectors"].items():
                self._raw_listener("Bank_" + page, binding, partial(self._select_page, page))
        for action, binding in self._profile.get("physical_buttons", {}).items():
            # These dedicated MPC transport controls are aliases, rather than
            # members of a pad page.  Invoke the same state changes as the
            # bundled MPC transport component directly: this avoids depending
            # on a second, virtual button element to relay an incoming CC.
            if action in ("play", "stop", "arrangement_record"):
                self._raw_listener("Physical_" + action, binding,
                    partial(self._physical_transport, action))
            else:
                self._raw_listener("Physical_" + action, binding,
                    lambda value, action=action: self._dispatch_pad_events([(action, value)]))

    def _physical_transport(self, action, value):
        if not value:
            return
        if action == "play":
            self.song.is_playing = not self.song.is_playing
        elif action == "stop":
            self.song.stop_playing()
        elif action == "arrangement_record":
            self.song.record_mode = not self.song.record_mode
        self.log_message("MPC physical {} pressed".format(action))

    def _bind_commands(self):
        self._listen("previous_device", partial(self._scroll_device, -1))
        self._listen("next_device", partial(self._scroll_device, 1))
        self._listen("device_lock", self._toggle_device_lock)
        self._listen("device_half", self._toggle_device_half)
        self._listen("mixer_half", self._toggle_mixer_half)
        self._listen("device_enable", self._toggle_device)
        self._listen("mute", partial(self._toggle_track_property, "mute"))
        self._listen("solo", partial(self._toggle_track_property, "solo"))
        self._listen("arm", partial(self._toggle_track_property, "arm"))
        self._listen("device_mode", partial(self._set_mode, "device"))
        self._listen("volume_mode", partial(self._set_mode, "volume"))
        self._listen("pan_mode", partial(self._set_mode, "pan"))
        self._listen("send_mode", self._cycle_send)
        self._listen("previous_track", partial(self._select_track, -1))
        self._listen("next_track", partial(self._select_track, 1))
        # Page A's pad transport goes through the shared pad router, so it
        # needs the same direct path as the physical transport CCs.
        self._listen("play", self._play)
        self._listen("stop", self._stop)
        self._listen("stop_track", self._stop_track)
        self._listen("status", self._show_status)
        self._listen("session_record", self._toggle_session_record)
        self._listen("continue", self._continue_playing)
        self._listen("tap_tempo", self._tap_tempo)
        self._listen("stop_all", self._stop_all_clips)
        self._listen("undo", self._undo_last)
        self._listen("redo", self._redo_last)
        self._listen("duplicate", self._duplicate_clip)
        self._listen("quantize", self._quantize_clip)
        for index in range(16):
            self._listen("clip_{}".format(index + 1), partial(self._launch_clip, index))
            self._listen("scene_{}".format(index + 1), partial(self._launch_scene, index))
        for action, tracks, scenes in (("session_left", -4, 0), ("session_right", 4, 0),
                                       ("session_up", 0, -4), ("session_down", 0, 4),
                                       ("scenes_previous", 0, -16), ("scenes_next", 0, 16)):
            self._listen(action, partial(self._move_session, tracks, scenes))
        self._listen("mixer_left", partial(self._move_mixer, -8))
        self._listen("mixer_right", partial(self._move_mixer, 8))
        for index in range(8):
            self._listen("track_{}".format(index + 1), partial(self._select_mixer_track, index))

    def _play(self):
        self.song.is_playing = not self.song.is_playing
        self.log_message("MPC pad play pressed")

    def _stop(self):
        self.song.stop_playing()
        self.log_message("MPC pad stop pressed")

    def _select_mixer_track(self, index):
        track = self._mixer.channel_strip(index).track
        if liveobj_valid(track):
            self.song.view.selected_track = track
            self.log_message("MPC selected mixer track {}".format(track.name))
            self._show_status()

    def _device_parameters_changed(self):
        if self._ready:
            self._refresh_parameters()

    def _refresh_parameters(self):
        if self._mode == "device":
            infos = four_parameters(self._device.parameters, self._device_half)
        else:
            infos = []
            for i in range(self._mixer_half * 4, self._mixer_half * 4 + 4):
                track = self._mixer.channel_strip(i).track
                parameter = None
                if liveobj_valid(track):
                    mixer = track.mixer_device
                    if self._mode == "volume":
                        parameter = mixer.volume
                    elif self._mode == "pan":
                        parameter = mixer.panning
                    elif self._send_index < len(mixer.sends):
                        parameter = mixer.sends[self._send_index]
                infos.append(ParameterInfo(parameter=parameter, name=parameter.name,
                                           default_encoder_sensitivity=1.0) if parameter else None)
        signature = (self._mode, self._device_half, self._mixer_half,
                     tuple(info.parameter if info else None for info in infos))
        if signature != self._mapping_signature:
            self._mapping_signature = signature
            self._parameter_provider.set_parameters(infos)
            self._show_status()

    def _set_mode(self, mode):
        self._mode = mode
        self._refresh_parameters()

    def _toggle_device_half(self):
        self._device_half = 1 - self._device_half
        self._set_mode("device")

    def _toggle_mixer_half(self):
        self._mixer_half = 1 - self._mixer_half
        if self._mode == "device":
            self._mode = "volume"
        self._refresh_parameters()

    def _cycle_send(self):
        self._send_index = (self._send_index + 1) % 4 if self._mode == "send" else 0
        self._set_mode("send")
        self._show_status()

    def _toggle_device(self):
        device = self._device.device()
        if liveobj_valid(device) and device.parameters:
            parameter = device.parameters[0]
            if parameter.is_enabled:
                parameter.value = 0 if parameter.value else 1

    def _scroll_device(self, delta):
        if self._device_locked:
            self.log_message("MPC device navigation blocked by lock")
            return
        if delta < 0:
            self._navigation.item_provider.scroll_left()
        else:
            self._navigation.item_provider.scroll_right()
        self._refresh_parameters()
        self.log_message("MPC device navigation {}".format("previous" if delta < 0 else "next"))

    def _toggle_device_lock(self):
        self._device_locked = not self._device_locked
        self.toggle_lock()
        self.log_message("MPC device lock {}".format("on" if self._device_locked else "off"))

    def _select_track(self, delta):
        tracks = tuple(self.song.visible_tracks) + tuple(self.song.return_tracks) + (self.song.master_track,)
        selected = self.song.view.selected_track
        index = tracks.index(selected) if selected in tracks else 0
        self.song.view.selected_track = tracks[max(0, min(index + delta, len(tracks) - 1))]

    def _stop_track(self):
        track = self.song.view.selected_track
        if track in self.song.tracks:
            track.stop_all_clips()

    def _toggle_track_property(self, name):
        track = self.song.view.selected_track
        if not liveobj_valid(track) or not hasattr(track, name):
            return
        if name == "arm" and not getattr(track, "can_be_armed", False):
            return
        setattr(track, name, not getattr(track, name))
        self.log_message("MPC {} {}".format(name, "on" if getattr(track, name) else "off"))

    def _launch_clip(self, index):
        # Physical pads number upward from the bottom-left.  Session scenes
        # number downward from the top, so translate the row here.
        track_index = self._session_ring.track_offset + index % 4
        scene_index = self._session_ring.scene_offset + 3 - index // 4
        tracks = tuple(self._session_ring.tracks_to_use())
        if track_index < len(tracks) and scene_index < len(self.song.scenes):
            track = tracks[track_index]
            if scene_index < len(track.clip_slots):
                track.clip_slots[scene_index].fire()
                self.log_message("MPC clip launch T{} S{}".format(track_index + 1, scene_index + 1))

    def _launch_scene(self, index):
        scene_index = self._session_ring.scene_offset + index
        if scene_index < len(self.song.scenes):
            self.song.scenes[scene_index].fire()
            self.log_message("MPC scene launch S{}".format(scene_index + 1))

    def _toggle_session_record(self):
        self.song.session_record = not self.song.session_record
        self.log_message("MPC session record {}".format("on" if self.song.session_record else "off"))

    def _continue_playing(self):
        # Match Live's bundled TransportComponent: Continue resumes when
        # stopped and stops when already playing.
        if self.song.is_playing:
            self.song.stop_playing()
        else:
            self.song.continue_playing()
        self.log_message("MPC continue {}".format("play" if self.song.is_playing else "stop"))

    def _tap_tempo(self):
        self.song.tap_tempo()
        self.log_message("MPC tap tempo")

    def _stop_all_clips(self):
        self.song.stop_all_clips()
        self.log_message("MPC stop all clips")

    def _undo_last(self):
        if self.song.can_undo:
            self.song.undo()
            self.log_message("MPC undo")

    def _redo_last(self):
        if self.song.can_redo:
            self.song.redo()
            self.log_message("MPC redo")

    def _selected_clip_slot(self):
        slot = self.song.view.highlighted_clip_slot
        return slot if liveobj_valid(slot) and slot.has_clip else None

    def _duplicate_clip(self):
        slot = self._selected_clip_slot()
        track = self.song.view.selected_track
        if slot is None or not liveobj_valid(track):
            return
        try:
            source_index = list(track.clip_slots).index(slot)
            target_index = track.duplicate_clip_slot(source_index)
            self.song.view.highlighted_clip_slot = track.clip_slots[target_index]
            self.song.view.detail_clip = track.clip_slots[target_index].clip
            self.log_message("MPC duplicate clip")
        except (Live.Base.LimitationError, RuntimeError, ValueError):
            pass

    def _quantize_clip(self):
        slot = self._selected_clip_slot()
        if slot is not None and slot.clip.is_midi_clip:
            slot.clip.quantize(Live.Song.RecordingQuantization.rec_q_sixtenth, 1.0)
            self.log_message("MPC quantize clip")

    def _move_session(self, tracks, scenes):
        ring = self._session_ring
        ring.set_offsets(bounded_offset(ring.track_offset, tracks, len(ring.tracks_to_use()), 4),
                         bounded_offset(ring.scene_offset, scenes, len(self.song.scenes), 4))
        self._show_status()

    def _move_mixer(self, delta):
        ring = self._mixer_ring
        # Preserve a full eight-track window at the end of a project.  With
        # twelve tracks, for example, the next window is tracks 5–12 and its
        # D16 half is tracks 9–12.
        ring.set_offsets(bounded_offset(ring.track_offset, delta, len(ring.tracks_to_use()), 8), 0)
        self._refresh_parameters()
        self._show_status()

    def _show_status(self):
        device = self._device.device()
        names = [info.name if info and info.parameter else "—" for info in self._parameter_provider.parameters]
        bank = self._device_bank_registry.get_device_bank(device) if liveobj_valid(device) else 0
        mode = self._mode if self._mode != "send" else "Send " + "ABCD"[self._send_index]
        selected = self.song.view.selected_track
        message = "MPC | Page {} | {} | {} | Bank {} {} | Q: {} | Clips T{} S{} | Mixer T{} {} | Selected {}".format(
            self._router.page, mode, device.name if liveobj_valid(device) else "No device", (bank or 0) + 1,
            "1–4" if self._device_half == 0 else "5–8", " / ".join(names),
            self._session_ring.track_offset + 1, self._session_ring.scene_offset + 1,
            self._mixer_ring.track_offset + 1, "1–4" if self._mixer_half == 0 else "5–8",
            selected.name if liveobj_valid(selected) else "—")
        self.show_message(message)
        if message != self._last_status:
            self.log_message(message)
            self._last_status = message

    def update_display(self):
        super(MPCKey37, self).update_display()
        if self._ready:
            # Mixer tracks/sends can change while a bank remains selected.
            try:
                with self.component_guard():
                    self._refresh_parameters()
                self._runtime_failed = False
            except (RuntimeError, ReferenceError):
                # Live objects may disappear between an event and a timer tick.
                self._mapping_signature = None
                if not self._runtime_failed:
                    self.log_message("MPC_Key_37 transient mapping error:\n" + traceback.format_exc())
                    self._runtime_failed = True

    def port_settings_changed(self):
        with self.component_guard():
            self._dispatch_pad_events(self._router.reset())
            for control in self._raw_buttons:
                control.release()
            for control in self._buttons.values():
                control.release()
            self._mapping_signature = None
            if self._ready:
                self._refresh_parameters()
        super(MPCKey37, self).port_settings_changed()

    def disconnect(self):
        self._ready = False
        for control, callback in self._callbacks:
            control.remove_value_listener(callback)
        self._callbacks = []
        self._dispatch_pad_events(self._router.reset())
        for control in self._buttons.values():
            control.release()
        super(MPCKey37, self).disconnect()
