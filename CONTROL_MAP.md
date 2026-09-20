# MPC Key 37 — Live quick reference

Pads count from the bottom-left: **1–4**, then upward through **13–16**. Press a bank button to select A–D. **Double-tap A** for E; one A press returns to A. **Double-tap D** for Performance: pads play an armed MIDI track on channel 10, following the drum rack's 4x4 grid from C1 (pad 1 = bottom-left); press any bank button to leave it.

| Page | Pads 1–4 | Pads 5–8 | Pads 9–12 | Pads 13–16 |
|---|---|---|---|---|
| **A — Device / transport** | Previous device; next device; previous bank; next bank | Q-Link half; lock; device on/off; Device Q-Link mode | Previous track; next track; Play; Stop | Session Record; Arrangement Record; Loop; Metronome |
| **B — Clips** | Lowest visible clip row | Next row | Next row | Top visible clip row |
| **C — Scenes** | Launch scenes 1–4 | Launch scenes 5–8 | Launch scenes 9–12 | Launch scenes 13–16 |
| **D — Mixer** | Select tracks 1–4 | Select tracks 5–8 | Mute; Solo; Arm; Stop selected track | Volume mode; Pan mode; Sends A–D mode; Q-Link track half |
| **E — Navigate / edit** | Clip grid left; right; up; down | Mixer tracks left; right; scenes previous 16; next 16 | Continue; Tap Tempo; Undo; Redo | Duplicate clip; Quantize clip; Stop All Clips; show status |
| **Performance** | Pads 1–16 play notes | Pads 1–16 play notes | Pads 1–16 play notes | Pads 1–16 play notes |

## Q-Links

- **Device mode**: Q-Links 1–4 control parameter slots 1–4. A5 switches them to slots 5–8.
- **Mixer mode**: D13 selects volume, D14 pan, D15 cycles sends A–D, and D16 switches Q-Links between tracks 1–4 and 5–8. Q1–Q4 always follow the active four-track half; D1–D8 only choose the track for D9–D12.
- Live’s **Pickup** takeover prevents jumps after changing a Q-Link target.

## Dedicated transport buttons

- **Play** toggles playback.
- **Stop** stops playback.
- **Record** toggles Arrangement Record.

## What maps directly to the official Force MPC behavior

Device banks, device navigation, locking, transport semantics, session/scene launching, mixer strip layout, and clip editing use the installed Live 12.4.6 Force MPC components or the same Live operations. The Key 37 has no established Force display/feedback protocol in Controller Mode, so pages, the double-A Page E gesture, and the four-Q-Link half-bank switch are adaptations.
