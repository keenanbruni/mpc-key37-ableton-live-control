# MPC Key 37 Ableton Live Control

Use the original MPC Key 37 as a hands-on control surface in Ableton Live.

Hardware-tested on macOS with the MPC in **Controller Mode**, Live 12.4.6, and the captured MPC Key 37 Controller Mode preset. The keyboard stays on MIDI channel 16; pads, Q-Links, and transport control Live. The Windows installer uses Ableton's supported script location, but Windows hardware testing is still needed.

## Install

1. On GitHub, choose **Code → Download ZIP** and unzip it.
2. Double-click the installer for your computer: **`Install MPC Key 37.command`** on macOS or **`Install MPC Key 37.bat`** on Windows. It installs the script and saves any previous version as a backup.
3. Restart Live.
4. In **Live Settings → Tempo & MIDI**, choose **MPC Key 37** in an empty Control Surface row. Select **MPC Key 37 Port 1** for Input and **None** for Output.
5. Set Live’s **Takeover Mode** to **Pickup**. Put the MPC in **Controller Mode**, then press Bank A.

If macOS asks before opening the installer, right-click it and choose **Open**. The installer copies only this script to:

`~/Music/Ableton/User Library/Remote Scripts/MPC_Key_37` on macOS, or
`C:\Users\you\Documents\Ableton\User Library\Remote Scripts\MPC_Key_37` on Windows.

It stores backups in the same User Library under `Remote Script Backups`.

### If the normal User Library is elsewhere

Run this from the downloaded folder:

```sh
# macOS
python3 tools/install.py --user-library "/path/to/your/Ableton User Library"

# Windows Command Prompt
py -3 tools\install.py --user-library "C:\path\to\your\Ableton User Library"
```

## Use

- **Bank A:** device control and transport
- **Bank B:** 4 × 4 clip launcher
- **Bank C:** scene launcher
- **Bank D:** tracks and mixer
- **Double-tap Bank A:** navigation, undo/redo, duplicate, quantize, and Stop All

Four Q-Links control the selected device, or four mixer tracks. In mixer mode, Q1–Q4 control tracks 1–4; after D16 they control tracks 5–8. D1–D8 select the track used by D9–D12. Turn a Q-Link through its current value once after changing targets; Pickup prevents parameter jumps.

See [CONTROL_MAP.md](CONTROL_MAP.md) for every pad assignment and [TUTORIAL_WALKTHROUGH.md](TUTORIAL_WALKTHROUGH.md) for a guided Live set.

## Troubleshooting

- **Nothing responds:** confirm Controller Mode, Port 1 as the Control Surface Input, then restart Live.
- **Keys also trigger commands:** set your instrument track’s MPC input to **channel 16**.
- **A knob appears inactive:** select a device, then rotate through its current value to pick it up.
- **Updating:** run the installer again. It preserves your installed MIDI profile and creates a backup first.

This is an independent community script. It does not install firmware, modify the MPC, or emulate Akai’s display protocol.
