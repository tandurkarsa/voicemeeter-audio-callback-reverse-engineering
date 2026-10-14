# Changelog

All notable changes to this project will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-10-14

### Added
- Initial release
- Complete reverse-engineering notes for Voicemeeter Audio Callback API
- Verified on Voicemeeter Potato 3.1.3.0 (Sept 2026)
- Working Python examples using `ctypes`:
  - `01_minimal_callback.py` — Hello world
  - `02_mode_explorer.py` — Test modes 0/1/2/4/7
  - `03_passthrough_audio.py` — Anti audio-disappear
  - `04_channel_meter.py` — Live 34-ch meter
- `CREDITS.md` — Human + AI attribution
- `docs/TEST_REPORT.md` — Verified test results

### Discovery Highlights
- Mode is **bit flag**: IN=1, OUT=2, MAIN=**4** (not sequential!)
- Command codes: 0x01, 0x02, 0x03, 0x0A, 0x0B, **0x14**
- Mode MAIN: nbi=**98**, nbo=**64**, passthrough offset **+34**
- Callback signature = **4 args** (2-arg version gives nCommand=0)
- Mode 0 = **invalid** (returns -100)

### Notes
This release produced with assistance from **DeepSeek AI**.
- Human: ideation, direction, real-hardware testing, debugging
- AI: reverse-engineering analysis, code generation, documentation
See [CREDITS.md](CREDITS.md).

### Known Limitations
- Only tested on Potato 3.1.3.0
- Banana/Basic support assumed (please verify + report)