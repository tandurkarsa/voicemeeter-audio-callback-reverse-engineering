# Quick Reference — Voicemeeter Audio Callback

**Print this. Tape it to your monitor.** 🖨️

---

## Mode Values (BIT FLAGS!)

```python
MODE_IN   = 1   # 0b001  → Command 0x0A, nbi=34, nbo=34
MODE_OUT  = 2   # 0b010  → Command 0x0B, nbi=64, nbo=64
MODE_MAIN = 4   # 0b100  → Command 0x14, nbi=98, nbo=64   ⭐
MODE_ALL  = 7   # 1|2|4  → Semua command
MODE_0    = 0   # ❌ INVALID (returns -100)
```

## Command Codes

```python
CB_STARTING = 0x01   # Stream start (init DSP)
CB_ENDING   = 0x02   # Stream end (cleanup)
CB_CHANGE   = 0x03   # Samplerate/buffer changed
CB_BUFFER_IN   = 0x0A   # Mode IN buffer
CB_BUFFER_OUT  = 0x0B   # Mode OUT buffer
CB_BUFFER_MAIN = 0x14   # Mode MAIN buffer
```

## Callback Signature (4 args!)

```python
from ctypes import c_long, c_void_p, WINFUNCTYPE

CALLBACK_TYPE = WINFUNCTYPE(
    c_long,     # return
    c_void_p,   # lpUser
    c_long,     # nCommand
    c_void_p,   # lpData
    c_long,     # nnn
)
```

## Buffer Struct

```python
class VBVMR_AUDIOBUFFER(Structure):
    _fields_ = [
        ("sr",  c_long),          # sample rate
        ("nbs", c_long),          # samples per frame
        ("nbi", c_long),          # num inputs
        ("nbo", c_long),          # num outputs
        ("r",   POINTER(c_float) * 128),  # read pointers
        ("w",   POINTER(c_float) * 128),  # write pointers
    ]
```

## Passthrough (Anti Audio-Disappear)

```python
# Mode IN / OUT: copy 1:1
for i in range(min(view.nbi, view.nbo)):
    view.outputs[i][:] = view.inputs[i][:]

# Mode MAIN: offset +34
for i in range(64):  # 8 bus × 8 ch
    view.outputs[i][:] = view.inputs[34 + i][:]
```

## DLL Path

```
C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll
C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote.dll
```

## Common Parameter Strings

```python
# Fader/mute
"Strip[0].Gain"     # -60..+12 dB
"Strip[0].Mute"     # 0/1
"Strip[0].Solo"     # 0/1
"Bus[0].Gain"       # -60..+12 dB
"Bus[0].Mute"       # 0/1

# Bus assignment
"Strip[0].A1"       # 0/1 (assign to bus A1)
"Strip[0].B1"       # 0/1

# Internal comp/gate
"Strip[0].Comp.Threshold"
"Strip[0].Gate.Threshold"

# Special commands
"Command.Restart"   # 1 = restart audio engine
"Command.Shutdown"  # 1 = quit Voicemeeter
```

## Relative Change (Bonus!)

```python
dll.VBVMR_SetParameterFloat(b"Strip[0].Gain += 3", c_float(0))   # +3 dB
dll.VBVMR_SetParameterFloat(b"Strip[0].Mute += 1", c_float(0))   # toggle
```

## Fade (Smooth)

```python
dll.VBVMR_SetParameterStringA(b"Strip[0].FadeTo", b"-10.0, 500")  # to -10dB in 500ms
dll.VBVMR_SetParameterStringA(b"Strip[0].FadeBy", b"-3.0, 200")   # by -3dB in 200ms
```

## Limits

- Max **3 apps** can register callback simultaneously
- Max **3 callbacks** per app (IN + OUT + MAIN)
- Callback thread: **non-reentrant**, real-time
- **Don't**: I/O, allocate memory, sleep, acquire locks

---

*Version: 1.0.0 | Voicemeeter 3.1.3.0*