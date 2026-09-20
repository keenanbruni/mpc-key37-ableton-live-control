# Changelog

## Unreleased

- Double-tap D opens a Performance page: pads play an armed MIDI track receiving channel 10 (with velocity and note-offs), while every other page keeps the pads consumed so control pages never double as instrument notes. Pads still held when leaving the Performance page keep playing until released, so notes cannot hang.
- The MPC's scattered hardware pad notes are translated to the drum grid (C1 upward in physical pad order) as they enter Live, so a 4x4 drum rack matches the pad layout on every page.

## 0.1.0 — 2026-09-19

First public release.

- Device, mixer, clip, scene, transport, and editing control for the original MPC Key 37.
- MPC Key 37 Controller Mode MIDI profile.
- macOS and Windows installers that preserve the previous installation.
- Control map and guided tutorial Live set.
