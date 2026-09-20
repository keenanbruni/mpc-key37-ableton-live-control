# MPC Key 37 Ableton Live tutorial
Howdy. Open `MPC Key 37 Tutorial.als` in Session View. It is a safe practice set: twelve tracks, two prepared scenes of blank MIDI clips, Drift for keyboard playback, and two Auto Filters for device control. Primarily meant for session view, although it works in arrangement too.

## Before you start

1. Put the MPC Key 37 in **Controller Mode**.
2. In Live's MIDI settings, select **MPC_Key_37** as the control surface, with MPC Key 37 Port 1 as its input. Leave **Takeover Mode** set to **Pickup**.
3. Use a short press of A, B, C, or D to open that page. **Double-tap A** to open Page E.
4. Pad numbers use the MPC's printed 1–16 labels. On B, the physical top row is pads 13–16.

## 20-minute first pass

### 1. Device page A (five minutes)

Select the first track, which contains two Auto Filters. Press **A8** for device control.

- **A1/A2**: step between the two Auto Filters.
- **A5**: switch the Q-Links between parameter slots 1–4 and 5–8.
- Turn Q2 slowly on the first Filter. Pickup takes over only after the knob reaches the current value, so the parameter will not jump.
- **A3/A4**: move to the preceding or following bank when a device has more than eight slots.
- **A6**: lock the current device; use A1/A2 to see that navigation does not change it. Press A6 again to unlock.
- **A7**: enable/bypass the selected device.
- **A9/A10**: select the preceding/following track. **A11/A12** play and stop. **A13–A16** are Session Record, Arrangement Record, Loop, and Metronome.

### 2. Clip and scene pages B/C (five minutes)

The set contains blank MIDI clips in scenes 1 and 2 on tracks 2–8.

- Press **B**. Pads 13–16 launch the top row of the current 4x4 window; pads 1–4 launch its bottom row. Start several clips, then use **E15** to stop them together.
- Press **C**. Pads 1–16 launch scenes 1–16. In this set, scenes 1 and 2 contain the prepared clips.
- Double-tap **A** for E, then use **E1–E4** to move the 4x4 clip window and **E7/E8** to move through sixteen-scene pages.

### 3. Mixer page D (five minutes)

Press **D**.

- **D1–D8** select the track used by D9–D12.
- **D9/D10/D11** toggle mute, solo, and arm on the selected track. **D12** stops that track's clip.
- **D13** maps Q1–Q4 to volume for tracks 1–4.
- **D14** maps Q1–Q4 to pan for tracks 1–4.
- **D15** maps Q1–Q4 to Sends A–D for tracks 1–4.
- **D16** switches the Q-Links to tracks 5–8.
- Double-tap **A**, press **E6**, then return to **D**: the mixer window becomes tracks 5–12. Press **D16** and Q1–Q4 now control tracks 9–12. **E5** moves back.


### 4. Keyboard, editing, and transport (five minutes)

Select the Drift track with **D2**. Its keyboard input is on MIDI channel 16, separate from the control commands. Play the physical keys to hear Drift.

With a MIDI clip selected:

- **E13** duplicates the selected clip.
- **E14** quantizes it to sixteenth notes.
- **E11/E12** undo and redo.
- **E9** continues playback, **E10** taps tempo, **E15** stops all clips, and **E16** writes the current mapping to Live's status bar.

The physical **Play**, **Stop**, and **Record** buttons provide the same core transport actions without changing pages.

## Control map

| Page | Purpose | Main controls |
|---|---|---|
| A | Device and transport | A1–A7 device navigation/banks/lock/bypass; A8 device mode; A9–A16 track and transport |
| B | Clip grid | 4x4 clip launch window |
| C | Scenes | 16-scene launch page |
| D | Mixer | D1–D8 select tracks; D9–D12 track actions; D13–D16 Q-Link modes |
| E | Navigation and editing | E1–E8 movement; E9–E16 transport, history, edit, stop, status |

For the full pad-by-pad reference, see `CONTROL_MAP.md`.

## Good practice habits

Start every session by pressing A, selecting the track/device you intend to control, and moving each Q-Link through its current value once. That makes Pickup predictable. If the MPC is reconnected after a disconnect, press A before continuing. Keep keyboard performance on the Drift track or another MIDI track receiving channel 16. Go nutz!
