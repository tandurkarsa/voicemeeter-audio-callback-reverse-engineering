# Voicemeeter Audio Callback — Reverse-Engineering Notes

> **Complete, verified documentation for Voicemeeter's Audio Callback API.**
> After days of trial-and-error, here's everything we found — so you don't have to.

[![Voicemeeter](https://img.shields.io/badge/Voicemeeter-3.1.3.0-blue)](https://vb-audio.com/Voicemeeter/potato.htm)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-yellow)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 What's This About?

Voicemeeter's Remote API has an **Audio Callback** feature that lets applications process audio in real-time, directly inside Voicemeeter's audio engine. It's powerful — it's how **Equalizer APO** works — but the official documentation is:

- ❌ Incomplete (some constants documented differently than runtime)
- ❌ Confusing (mode values don't match many sources)
- ❌ Missing working examples in most languages

This repo documents **what actually works**, verified empirically on Voicemeeter **3.1.3.0** (September 2026) with Python + `ctypes`.

---

## ⚡ TL;DR — 5 Key Findings

1. **Mode is a BIT FLAG**, not sequential: `IN=1, OUT=2, MAIN=4`
2. **Command codes**: `STARTING=0x01, ENDING=0x02, CHANGE=0x03, BUFFER_IN=0x0A, BUFFER_OUT=0x0B, BUFFER_MAIN=0x14`
3. **Mode MAIN**: `nbi=98` (34 strips + 64 bus), `nbo=64`. **Passthrough offset +34!**
4. **Signature is 4 args**: `(void* lpUser, long nCommand, void* lpData, long nnn)`
5. **Always auto-passthrough** (copy input → output) or **audio will disappear**

Full write-up → [`docs/VOICEMEETER_API_NOTES.md`](docs/VOICEMEETER_API_NOTES.md)

---

## 🚀 Quick Start

### Prerequisites
- **Voicemeeter Potato / Banana / Basic** (version **3.1.3.0** or newer)
- Python 3.8+
- `pip install numpy`

### Run the Minimal Example

```bash
git clone https://github.com/YOUR_USERNAME/voicemeeter-audio-callback-reverse-engineering.git
cd voicemeeter-audio-callback-reverse-engineering
pip install -r requirements.txt
python examples/01_minimal_callback.py
```

**What it does:** Registers a callback, prints incoming buffer stats. Voicemeeter must be **running + audio playing**.

### Explore All Modes

```bash
python examples/02_mode_explorer.py
```

**What it does:** Tries modes 0, 1, 2, 4, 7 → shows which command codes you get + channel counts. This is the "reality check" script.

### Test Passthrough (Fix Audio Disappearing)

```bash
python examples/03_passthrough_audio.py
```

**What it does:** Registers mode MAIN + auto-passthrough. Audio keeps playing normally while callback is active.

---

## 📚 Repo Structure

```
.
├── README.md                         ← This file
├── LICENSE                           ← MIT
├── CONTRIBUTING.md                   ← How to help
├── CHANGELOG.md                      ← Version history
├── requirements.txt                  ← numpy
├── docs/
│   ├── VOICEMEETER_API_NOTES.md      ← Full technical documentation
│   └── QUICK_REFERENCE.md            ← Cheat sheet (1 page)
└── examples/
    ├── 01_minimal_callback.py        ← Hello world
    ├── 02_mode_explorer.py           ← Test all modes
    ├── 03_passthrough_audio.py       ← Anti audio-disappear
    └── 04_channel_meter.py           ← Real-time level meter
```

---

## 🧪 What We Verified

| Finding | Value | Test |
|---|---|---|
| Mode IN (bit flag) | `1` | ✅ Command `0x0A`, nbi=34 |
| Mode OUT (bit flag) | `2` | ✅ Command `0x0B`, nbi=64 |
| **Mode MAIN (bit flag)** | **`4`** | ✅ Command `0x14`, **nbi=98, nbo=64** |
| Mode 0 | **INVALID** | ❌ Returns -100 |
| Mode 7 (IN\|OUT\|MAIN) | `7` | ✅ All commands |
| Signature | 4 args | ✅ Without this, nCommand always = 0 |
| Passthrough MAIN | offset +34 | ✅ No audio leak to center/LFE |

---

## 🚨 Common Pitfalls

### ❌ Wrong: Assuming mode values are 0/1/2 (sequential)
```python
mode = 2  # "I want MAIN" — NO! This is OUTPUT INSERT
```
### ✅ Right: Use bit flags
```python
mode = 4  # MAIN (all I/O)
```

### ❌ Wrong: 2-arg callback signature
```python
CALLBACK_TYPE = WINFUNCTYPE(c_long, c_long, c_void_p)  # MISSING ARGS
```
Result: `nCommand` always = 0.

### ✅ Right: 4-arg signature
```python
CALLBACK_TYPE = WINFUNCTYPE(c_long, c_void_p, c_long, c_void_p, c_long)
```

### ❌ Wrong: Reading `r[i]` as if it maps to `w[i]` in MAIN mode
```python
outputs[i] = inputs[i]  # Audio leaks to random channels
```
### ✅ Right: MAIN mode has different layouts
```python
outputs[i] = inputs[34 + i]  # Skip strip channels, take bus channels
```

---

## 🎓 Who Is This For?

- 🎛️ **Audio developers** building Voicemeeter integrations
- 🐍 **Python devs** wanting real-time DSP on Windows
- 🦀 **Rust / C# / JS devs** — findings are language-agnostic, only the wrapper differs
- 🔬 **Reverse-engineers** curious about how audio callbacks work
- 🎚️ **DIY mixer builders** (this repo was born from the "Swara 34" project)

---

## 🔗 Related Projects

- [Voicemeeter Official](https://vb-audio.com/Voicemeeter/) — by Vincent Burel
- [VB-Audio Forum](https://forum.vb-audio.com/) — Official forum
- [voicemeeter-api-python](https://github.com/onyx-and-iris/voicemeeter-api-python) — Python wrapper (no callback support)
- [Voicemeeter-AudioCallback-Simple-Example](https://github.com/A-tG/Voicemeeter-AudioCallback-Simple-Example) — C# example
- [Equalizer APO](https://sourceforge.net/projects/equalizerapo/) — Uses Audio Callback in production

---

## 🙏 Contributing

Found something new? Different Voicemeeter version? Different OS? **Open an issue or PR!**

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Especially welcome:
- Testing on **Voicemeeter Banana** / **Basic**
- Testing on older versions (< 3.1.3.0)
- Wrappers for other languages (Rust, C#, Node.js, Go)
- Corrections if you find different behavior

---

## ⚖️ License & Attribution

- **This documentation**: MIT (use freely)
- **Voicemeeter Remote API**: © Vincent Burel / VB-Audio Software
  - Free to use in any project (commercial since March 2021)
  - See [VoicemeeterRemoteAPI.pdf](https://github.com/vburel2018/Voicemeeter-SDK/blob/main/VoicemeeterRemoteAPI.pdf)

**This project is NOT affiliated with VB-Audio.**

---

## 🙏 Credits

This project is a **human-AI collaboration**:

- **Ideation, direction, verification, execution** — by the human contributor ([@YOUR_USERNAME](https://github.com/YOUR_USERNAME))
- **Reverse-engineering, code generation, documentation** — by **DeepSeek AI** (deepseek-chat)

We believe in **transparent attribution of AI involvement** in open-source
projects. See [CREDITS.md](CREDITS.md) for the full breakdown.

If you find this useful, please ⭐ star the repo — it helps others find it!

---

## ⭐ Star History

If this repo saved you hours of debugging, please ⭐ star it — helps others find it!

---

*Generated from the [Swara 34](https://github.com/tandurkarsa/swara34) project — a digital mixer console for Voicemeeter.*
