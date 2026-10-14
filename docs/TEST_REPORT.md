# Test Report

## Test Environment

| Item | Value |
|---|---|
| OS | Windows 11 (64-bit) |
| Voicemeeter | Potato 3.1.3.0 (Sept 2026) |
| Python | 3.13 |
| numpy | Latest |

## Verified by Real-Hardware Testing

### ✅ Confirmed Working

| Test | Script | Result |
|---|---|---|
| DLL load + Login | `01_minimal_callback.py` | ✅ |
| Register mode=MAIN (4) | `01_minimal_callback.py` | ✅ |
| Command 0x14 received | `01_minimal_callback.py` | ✅ |
| Buffer info: nbi=98, nbo=64 | `01_minimal_callback.py` | ✅ |
| Mode 0 → return -100 | `02_mode_explorer.py` | ✅ |
| Mode 1 → command 0x0A | `02_mode_explorer.py` | ✅ |
| Mode 2 → command 0x0B | `02_mode_explorer.py` | ✅ |
| Mode 4 → command 0x14 | `02_mode_explorer.py` | ✅ |
| Passthrough (no audio disappear) | `03_passthrough_audio.py` | ✅ |
| No channel leak (no center/LFE audio) | `03_passthrough_audio.py` | ✅ |
| 34-channel peak meter | `04_channel_meter.py` | ✅ |

### ⚠️ Not Yet Tested

| Test | Why Not |
|---|---|
| Banana compatibility | Only Potato hardware available |
| Basic compatibility | Only Potato hardware available |
| Older Voicemeeter (< 3.1.3.0) | Only 3.1.3.0 tested |
| Multi-app coexistence (3 slots) | Not enough apps to test |
| 32-bit Python + VoicemeeterRemote.dll | Only 64-bit tested |

**If you test these and find differences → please open an issue!**

## Static Analysis (Code Review)

All Python examples were reviewed for:
- ✅ Import correctness
- ✅ ctypes type mapping
- ✅ Constant values (verified against SDK header)
- ✅ Logic flow (traced through all branches)
- ✅ Error handling (try/except, cleanup)

**Known limitation:** We can't run automated tests in CI because
Voicemeeter requires Windows + real audio hardware.

## Reproduction Steps

To reproduce the findings:

1. Install Voicemeeter Potato 3.1.3.0
2. Play music through Voicemeeter (via VAIO or hardware input)
3. Run `python examples/02_mode_explorer.py`
4. Compare output with "Expected" section in README

## Reporting a Bug

If you find behavior that **differs from what's documented here**:

1. Open an issue
2. Include:
   - Voicemeeter version
   - OS + bitness
   - Python version
   - Full console output
   - What you expected vs. what happened

We especially want to know if:
- **Voicemeeter Banana** behaves differently
- **Older versions** have different constants
- **32-bit** has different behavior

---

*Last updated: 2026-10-14*