# Voicemeeter Remote API + Audio Callback — Catatan Lengkap

> **Status:** Verified working dengan Voicemeeter **3.1.3.0** (September 2026)
> **Platform:** Windows 10/11 (64-bit), Python 3.13+
> **Konteks:** Hasil reverse-engineering + verifikasi empiris untuk proyek Swara 34

---

## 📋 Daftar Isi

1. [Ringkasan Eksekutif](#1-ringkasan-eksekutif)
2. [Setup & Instalasi](#2-setup--instalasi)
3. [Setup DLL & Login](#3-setup-dll--login)
4. [Audio Callback — Konsep Dasar](#4-audio-callback--konsep-dasar)
5. [⭐ Mode Callback = BIT FLAG (Temuan Terbesar)](#5--mode-callback--bit-flag-temuan-terbesar)
6. [Konstanta Command](#6-konstanta-command)
7. [Buffer Layout per Mode](#7-buffer-layout-per-mode)
8. [Signature Callback yang Benar](#8-signature-callback-yang-benar)
9. [Teknik Passthrough (Anti Audio-Hilang)](#9-teknik-passthrough-anti-audio-hilang)
10. [Parameter API — Cheat Sheet](#10-parameter-api--cheat-sheet)
11. [Pitfalls & Gotchas](#11-pitfalls--gotchas)
12. [Debug Checklist](#12-debug-checklist)
13. [Contoh Kode Minimal (Copy-Paste)](#13-contoh-kode-minimal-copy-paste)
14. [Referensi SDK & Sumber Belajar](#14-referensi-sdk--sumber-belajar)

---

## 1. Ringkasan Eksekutif

**Voicemeeter Remote API** memungkinkan aplikasi pihak ketiga untuk:
- ✅ Baca/tulis parameter mixer (gain, mute, bus send, EQ, dll)
- ✅ **Proses audio real-time** via **Audio Callback** (insert FX / analyser)
- ✅ Kontrol device audio (input/output enumeration)
- ✅ Kirim/terima MIDI & Macro Buttons

**Audio Callback** adalah fitur yang paling powerful dan paling jarang dipakai. Hanya ~3 aplikasi bisa register sekaligus. Dokumentasi resmi kurang lengkap — beberapa nilai konstanta di dokumen lama **berbeda** dari yang dipakai di runtime.

Dokumen ini adalah hasil dari reverse-engineering selama beberapa hari, dengan verifikasi empiris pada Voicemeeter 3.1.3.0.

---

## 2. Setup & Instalasi

### Yang Dibutuhkan
- **Voicemeeter Potato** terinstall (versi 3.1.3.0 atau lebih baru)
- Python 3.8+ (tested di 3.13)
- Numpy: `pip install numpy`

### File yang Dibutuhkan
```
C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll   (64-bit)
C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote.dll     (32-bit)
```

⚠️ **Keduanya ada!** Pilih berdasarkan Python bit-ness:
```python
import ctypes
bits = 8 * ctypes.sizeof(ctypes.c_void_p)
dll_name = "VoicemeeterRemote64.dll" if bits == 64 else "VoicemeeterRemote.dll"
```

---

## 3. Setup DLL & Login

### Cara Load DLL

```python
import ctypes
from ctypes import c_long, c_float, c_char_p, c_void_p, POINTER, WINFUNCTYPE

dll = ctypes.WinDLL(r"C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll")

# Set argtypes & restype untuk semua fungsi
dll.VBVMR_Login.restype = c_long
dll.VBVMR_Login.argtypes = []

dll.VBVMR_GetParameterFloat.restype = c_long
dll.VBVMR_GetParameterFloat.argtypes = [c_char_p, POINTER(c_float)]

dll.VBVMR_SetParameterFloat.restype = c_long
dll.VBVMR_SetParameterFloat.argtypes = [c_char_p, c_float]

# Audio callback
dll.VBVMR_AudioCallbackRegister.restype = c_long
dll.VBVMR_AudioCallbackRegister.argtypes = [c_long, CALLBACK_TYPE, c_void_p, c_char_p]

dll.VBVMR_AudioCallbackStart.restype = c_long
dll.VBVMR_AudioCallbackStart.argtypes = []

dll.VBVMR_AudioCallbackStop.restype = c_long
dll.VBVMR_AudioCallbackStop.argtypes = []

dll.VBVMR_AudioCallbackUnregister.restype = c_long
dll.VBVMR_AudioCallbackUnregister.argtypes = []
```

### Login / Logout

```python
ret = dll.VBVMR_Login()
# ret == 0  → OK, Voicemeeter running
# ret == 1  → OK, tapi Voicemeeter belum dijalankan
# ret < 0   → ERROR

# ... lakukan sesuatu ...

dll.VBVMR_Logout()
```

⚠️ **ATURAN:** Login sekali di awal aplikasi, logout sekali di akhir. **Jangan** login/logout berulang-ulang.

---

## 4. Audio Callback — Konsep Dasar

### Fungsi Terkait

| Fungsi | Kegunaan |
|---|---|
| `VBVMR_AudioCallbackRegister(mode, cb, lpUser, szClientName)` | Daftarkan callback |
| `VBVMR_AudioCallbackStart()` | Mulai stream audio |
| `VBVMR_AudioCallbackStop()` | Hentikan stream |
| `VBVMR_AudioCallbackUnregister()` | Lepas callback |

### Batasan Keras

| Batasan | Nilai | Catatan |
|---|---|---|
| **Maksimum aplikasi** yang bisa register | **3** | Termasuk Voicemeeter sendiri |
| **Maksimum callback** per aplikasi | **3** | IN + OUT + MAIN |
| **Thread** | 1 (time-critical) | Callback non-reentrant |
| **Time budget** | ~80% buffer duration | 2048 samples @ 48kHz = ~42 ms, budget ~34 ms |
| **Operasi terlarang** di callback | I/O, alokasi memori, blocking | Bisa bikin audio drop-out |

---

## 5. ⭐ Mode Callback = BIT FLAG (Temuan Terbesar)

### 🚨 INI TEMUAN PALING PENTING 🚨

**Mode callback adalah bit flag, bukan nilai sequential!**

Banyak developer (dan dokumentasi lama) salah paham ini. Nilai yang benar:

| Konstanta | Nilai | Binary | Arti |
|---|---|---|---|
| `VBVMR_AUDIOCALLBACK_IN` | **1** | `0b001` | Input Insert |
| `VBVMR_AUDIOCALLBACK_OUT` | **2** | `0b010` | Output Insert |
| `VBVMR_AUDIOCALLBACK_MAIN` | **4** | `0b100` | Main Stream |

### Kombinasi via Bit OR

```python
# Input + Output insert sekaligus:
mode = 1 | 2  # = 3

# Semua stream:
mode = 1 | 2 | 4  # = 7

# Hanya main stream:
mode = 4  # ← INI YANG BENAR UNTUK MAIN! Bukan 2!
```

### ⚠️ Konsekuensi Salah Paham

| Yang Developer Kira | Kenyataan |
|---|---|
| Mode 0 = Input Insert | ❌ Mode 0 = **INVALID**, return -100 |
| Mode 1 = Output Insert | ❌ Mode 1 = **Input Insert** |
| Mode 2 = Main Stream | ❌ Mode 2 = **Output Insert** |
| — | ✅ Mode 4 = **Main Stream** |

### Bukti dari Header SDK

```c
// VoicemeeterRemote.h
#define VBVMR_AUDIOCALLBACK_IN   (1)
#define VBVMR_AUDIOCALLBACK_OUT  (2)
#define VBVMR_AUDIOCALLBACK_MAIN (4)
```

### Test Empiris

```
mode=0  → Register FAIL (ret=-100)
mode=1  → Command 0x0A (BUFFER_IN),   nbi=34, nbo=34
mode=2  → Command 0x0B (BUFFER_OUT),  nbi=64, nbo=64
mode=4  → Command 0x14 (BUFFER_MAIN), nbi=98, nbo=64   ← BENAR!
mode=7  → Semua command muncul
```

---

## 6. Konstanta Command

### Nilai Resmi (Verified Empiris)

```c
VBVMR_CBCOMMAND_STARTING    = 0x01   // Stream mulai (first call)
VBVMR_CBCOMMAND_ENDING      = 0x02   // Stream berakhir (last call)
VBVMR_CBCOMMAND_CHANGE      = 0x03   // Sample rate / buffer size berubah
VBVMR_CBCOMMAND_BUFFER_IN   = 0x0A   // Buffer untuk mode IN (10 desimal)
VBVMR_CBCOMMAND_BUFFER_OUT  = 0x0B   // Buffer untuk mode OUT (11 desimal)
VBVMR_CBCOMMAND_BUFFER_MAIN = 0x14   // Buffer untuk mode MAIN (20 desimal)
```

### ⚠️ Konstanta Lama yang SALAH

Beberapa sumber (termasuk PDF X.1.2.9 halaman 27) menyebut:
```
0x04, 0x08, 0x10  ← INI SALAH untuk runtime!
```

Test empiris menunjukkan yang benar: `0x0A`, `0x0B`, `0x14`.

**Selalu verifikasi dengan log command asli!** Jangan percaya dokumentasi 100%.

### Cara Log Semua Command

```python
def debug_callback(lpUser, nCommand, lpData, nnn):
    print(f"CMD: 0x{nCommand:02X} ({nCommand})")
    return 0
```

---

## 7. Buffer Layout per Mode

### Struct Buffer

```c
typedef struct tagVBVMR_AUDIOBUFFER {
    long   audiobuffer_sr;      // Sample rate (48000, 44100, ...)
    long   audiobuffer_nbs;     // Frame count per callback (2048, 512, ...)
    long   audiobuffer_nbi;     // Jumlah channel INPUT
    long   audiobuffer_nbo;     // Jumlah channel OUTPUT
    float *audiobuffer_r[128];  // Array pointer baca (per channel)
    float *audiobuffer_w[128];  // Array pointer tulis (per channel)
} VBVMR_T_AUDIOBUFFER;
```

**Data format:** Planar `float32` — array `r[i]` berisi `nbs` sample float32 untuk channel i. **Bukan interleaved.**

### Mode IN (`0x0A`)

```
nbi = nbo = 34 (Potato) / 22 (Banana) / 10 (Basic)
├─ r[0..nbi-1]  = sample input semua strip
└─ w[0..nbo-1]  = output (write back untuk proses)

Layout: copy 1:1 (r[i] → w[i])
```

### Mode OUT (`0x0B`)

```
nbi = nbo = 64 (Potato) / 40 (Banana) / 16 (Basic)
├─ r[0..63] = sample pre-master dari semua bus
│             (8 bus × 8 ch: FL,FR,C,LFE,RL,RR,SL,SR)
└─ w[0..63] = output bus

Layout: copy 1:1 (r[i] → w[i])
```

### Mode MAIN (`0x14`) — ⚠️ KHUSUS

```
nbi = 98 (Potato)   ← 34 strip + 64 bus
nbo = 64            ← 64 bus saja

┌────────────────────────────────────────────┐
│  INPUT (nbi = 98)                          │
│  ┌────────────────────┐ ┌────────────────┐ │
│  │ r[0..33]           │ │ r[34..97]      │ │
│  │ 34 strip (HW+VAIO) │ │ 64 bus (read)  │ │
│  └────────────────────┘ └────────────────┘ │
└────────────────────────────────────────────┘
                    │
                    │  PASSTHROUGH:
                    │  w[i] = r[34 + i]
                    │  (offset +34!)
                    ▼
┌────────────────────────────────────────────┐
│  OUTPUT (nbo = 64)                         │
│  w[0..63] = 64 bus (write)                 │
└────────────────────────────────────────────┘
```

**🚨 JANGAN copy 1:1 di mode MAIN!** Karena:
- `r[0..33]` = strip audio (bukan bus)
- `r[34..97]` = bus audio (yang harus di-copy ke output)
- Kalau salah, audio bisa muncul di channel acak (center/LFE)

---

## 8. Signature Callback yang Benar

### Signature Resmi (dari SDK Header)

```c
typedef long (__stdcall *T_VBVMR_VBAUDIOCALLBACK)(
    void *lpUser,    // User pointer (yang kamu pass saat register)
    long nCommand,   // Command code (0x01, 0x0A, 0x14, dll)
    void *lpData,    // Pointer ke VBVMR_AUDIOBUFFER atau VBVMR_AUDIOINFO
    long nnn         // Additional data, unused (= 0)
);
```

### ⚠️ Common Mistake

**SALAH:**
```python
CALLBACK_TYPE = WINFUNCTYPE(c_long, c_long, c_void_p)  # 2 argumen
```

**BENAR:**
```python
from ctypes import c_long, c_void_p, WINFUNCTYPE
CALLBACK_TYPE = WINFUNCTYPE(
    c_long,     # return type
    c_void_p,   # lpUser
    c_long,     # nCommand
    c_void_p,   # lpData
    c_long,     # nnn
)
```

Kalau salah signature, `nCommand` akan **selalu 0** (karena Python membaca `lpUser` = NULL sebagai command).

### Wrapper Python Lengkap

```python
def _cb(lpUser, nCommand, lpData, nnn):
    try:
        if nCommand == 0x01:  # STARTING
            pass  # init
        elif nCommand == 0x02:  # ENDING
            pass  # cleanup
        elif nCommand == 0x03:  # CHANGE (samplerate/buffer berubah)
            pass
        elif nCommand == 0x0A:  # BUFFER_IN
            view = AudioBufferView(lpData, is_input=True)
            passthrough_buffer(view, mode='in')
        elif nCommand == 0x0B:  # BUFFER_OUT
            view = AudioBufferView(lpData, is_input=True)
            passthrough_buffer(view, mode='out')
        elif nCommand == 0x14:  # BUFFER_MAIN
            view = AudioBufferView(lpData, is_input=True)
            passthrough_buffer(view, mode='main')  # ← special!
        return 0
    except Exception as e:
        # JANGAN crash — bisa bikin audio drop-out
        return 0

cb_ref = CALLBACK_TYPE(_cb)  # WAJIB simpan referensi agar tidak GC
```

### ⚠️ Jangan Lupa Simpan Referensi!

```python
self._callback_ref = CALLBACK_TYPE(_cb)  # ✅ Simpan di self
# self._callback_ref = None → bisa di-GC oleh Python → crash!
```

---

## 9. Teknik Passthrough (Anti Audio-Hilang)

### Masalah
Kalau kita register callback tapi **tidak menulis ke buffer output**, audio akan **hilang total** (silence). Voicemeeter berasumsi callback bertanggung jawab atas output.

### Solusi: Auto-Passthrough

Sebelum menjalankan DSP, **copy dulu input ke output**. Ini yang membuat audio tetap terdengar.

```python
def passthrough_buffer(view, kind='potato', mode=None):
    """Copy input → output sesuai mode."""

    # ── Mode MAIN: offset +34 ──
    if view.nbi >= 98 and view.nbo >= 64:
        # Strip audio di r[0..33], bus audio di r[34..97]
        for i in range(64):  # 8 bus × 8 ch
            src = view.inputs[34 + i]
            dst = view.outputs[i]
            if src is not None and dst is not None:
                dst[:] = src[:]
        return

    # ── Mode IN / OUT: copy 1:1 ──
    n = min(view.nbi, view.nbo)
    for i in range(n):
        src = view.inputs[i]
        dst = view.outputs[i]
        if src is not None and dst is not None:
            dst[:] = src[:]
```

**Pola eksekusi:**
1. Auto-passthrough (output terisi)
2. Panggil user handler (DSP bisa override output kalau mau)

---

## 10. Parameter API — Cheat Sheet

### Get / Set Parameter Float

```python
# Format string parameter:
# Strip[N].parameter      → N = index strip (0-based)
# Bus[N].parameter        → N = index bus (0-based)

# Contoh:
dll.VBVMR_SetParameterFloat(b"Strip[0].Gain", c_float(-6.0))
dll.VBVMR_SetParameterFloat(b"Strip[0].Mute", c_float(1.0))
dll.VBVMR_SetParameterFloat(b"Bus[0].Gain", c_float(0.0))
```

### Parameter Umum

| Parameter | Nilai | Keterangan |
|---|---|---|
| `Strip[i].Gain` | -60 .. +12 dB | Gain fader |
| `Strip[i].Mute` | 0 / 1 | Mute |
| `Strip[i].Solo` | 0 / 1 | Solo |
| `Strip[i].Mono` | 0 / 1 | Mono |
| `Strip[i].A1`..`A5` | 0 / 1 | Assign ke bus A |
| `Strip[i].B1`..`B3` | 0 / 1 | Assign ke bus B |
| `Strip[i].Label` | String | Label strip |
| `Bus[i].Gain` | -60 .. +12 dB | Gain bus |
| `Bus[i].Mute` | 0 / 1 | Mute bus |
| `Bus[i].mode.normal` | 0 / 1 | Bus mode normal |
| `Bus[i].mode.Composite` | 0 / 1 | Composite mode |
| `Bus[i].mode.UpMix21` | 0 / 1 | Upmix 2.1 |
| `Bus[i].mode.UpMix41` | 0 / 1 | Upmix 4.1 |
| `Bus[i].mode.UpMix61` | 0 / 1 | Upmix 6.1 |
| `Strip[i].Comp` | 0 .. 10 | Internal comp knob |
| `Strip[i].Comp.Threshold` | -40 .. -3 dB | Comp threshold |
| `Strip[i].Gate` | 0 .. 10 | Internal gate knob |
| `Strip[i].Gate.Threshold` | -60 .. -10 dB | Gate threshold |
| `Strip[i].EQGain1` | -12 .. +12 dB | Virtual strip EQ |
| `Strip[i].Reverb` | 0 .. 10 | Reverb send |
| `Strip[i].Delay` | 0 .. 10 | Delay send |
| `Strip[i].Fx1` / `.Fx2` | 0 .. 10 | External FX send |

### Relative Change (Bonus!)

```python
# Tambah/kurang nilai relatif:
dll.VBVMR_SetParameterFloat(b"Strip[0].Gain += 3", c_float(0))  # tambah 3 dB
dll.VBVMR_SetParameterFloat(b"Strip[0].Gain -= 3", c_float(0))  # kurang 3 dB

# Atau toggle:
dll.VBVMR_SetParameterFloat(b"Strip[0].Mute += 1", c_float(0))  # toggle mute
```

### Special Command

```python
dll.VBVMR_SetParameterFloat(b"Command.Shutdown", c_float(1))   # tutup VM
dll.VBVMR_SetParameterFloat(b"Command.Show", c_float(1))       # show window
dll.VBVMR_SetParameterFloat(b"Command.Restart", c_float(1))    # restart audio engine
dll.VBVMR_SetParameterFloat(b"Command.Save", c_float(1))       # save config
```

### Fade (Smooth Transition)

```python
# FadeTo: fade ke nilai target dalam waktu tertentu
# Format: "target, ms"
dll.VBVMR_SetParameterStringA(b"Strip[0].FadeTo", b"-10.0, 500")  # fade ke -10 dB dalam 500ms

# FadeBy: fade relatif
dll.VBVMR_SetParameterStringA(b"Strip[0].FadeBy", b"-3.0, 200")   # turun 3 dB dalam 200ms
```

---

## 11. Pitfalls & Gotchas

### 🚫 1. Mode 0 = Invalid
Jangan pakai mode 0. Selalu pakai 1, 2, 4, atau kombinasi.

### 🚫 2. Jangan Lupa Simpan `_callback_ref`
```python
# ❌ SALAH:
dll.VBVMR_AudioCallbackRegister(mode, CALLBACK_TYPE(_cb), None, b"S34")
# _cb akan di-GC → crash setelah beberapa saat

# ✅ BENAR:
self._cb_ref = CALLBACK_TYPE(_cb)
dll.VBVMR_AudioCallbackRegister(mode, self._cb_ref, None, b"S34")
```

### 🚫 3. Slot Callback Terbatas (Max 3)
Kalau register gagal dengan `-100`:
- Ada aplikasi lain yang sudah pakai (EqualizerAPO, MacroButtons, dll)
- Coba kill: `taskkill /F /IM VoicemeeterMacroButtons.exe`
- Restart Voicemeeter

### 🚫 4. Jangan Blocking di Callback
```python
def _cb(...):
    # ❌ JANGAN:
    print("test")           # I/O
    file.write(data)        # I/O
    time.sleep(0.1)         # blocking
    np.zeros(1024)          # alokasi memori
    lock.acquire()          # bisa blocking

    # ✅ BOLEH:
    buffer[i] = value       # komputasi
    np.copyto(dst, src)     # zero-copy
    return 0
```

### 🚫 5. Exception Harus Di-Catch
```python
def _cb(...):
    try:
        # ... semua kode ...
    except Exception as e:
        # JANGAN re-raise! Bisa crash audio thread
        log.error(f"CB error: {e}")
    return 0
```

### 🚫 6. Mode MAIN Butuh Offset +34
```python
# ❌ SALAH di mode MAIN:
for i in range(64):
    outputs[i] = inputs[i]   # audio nyasar!

# ✅ BENAR:
for i in range(64):
    outputs[i] = inputs[34 + i]   # bus audio
```

### 🚫 7. Buffer Tidak Persist
Setiap callback, pointer `r[i]` dan `w[i]` mungkin berubah. **Jangan cache** pointer antar callback.

```python
# ❌ SALAH:
cached_ptr = view.inputs[0]  # simpan untuk callback berikutnya

# ✅ BENAR:
# Akses ulang setiap callback
for i in range(view.nbi):
    process(view.inputs[i])
```

### ⚠️ 8. Kalau Sample Rate Berubah → Command 0x03
Kalau user ganti output device A1, sample rate bisa berubah. Voicemeeter kirim command `0x03` (CHANGE). **Reset semua state DSP** (envelope, filter history) untuk hindari klik.

```python
elif nCommand == 0x03:  # CHANGE
    # Reset semua DSP state
    for dsp in all_dsps:
        dsp.reset()
```

### ⚠️ 9. Voicemeeter Bisa Restart → Command 0x02 → 0x01
Kalau VM restart (misalnya user ubah setting audio), stream akan:
1. ENDING (0x02) — cleanup
2. STARTING (0x01) — init ulang

Pastikan handler Anda idempotent.

### ⚠️ 10. Don't Trust the Docs 100%
PDF X.1.2.9 punya error:
- Command values berbeda
- Mode sequential ≠ bit flag
- Dokumentasi lama

**Selalu verifikasi empiris!**

---

## 12. Debug Checklist

Kalau callback tidak bekerja, cek ini secara berurutan:

- [ ] **Login OK?** — `dll.VBVMR_Login() == 0 atau 1`
- [ ] **DLL versi terbaru?** — minimal 3.1.3.0
- [ ] **Slot callback tidak penuh?** — `tasklist | findstr voicemeeter`
- [ ] **Register return 0?** — kalau 1 = sudah dipakai, kalau -100 = slot penuh
- [ ] **Start return 0?** — kalau -2 = belum register
- [ ] **Command masuk?** — pasang log di callback
- [ ] **Command value benar?** — 0x01, 0x02, 0x03, 0x0A, 0x0B, 0x14
- [ ] **`nbi` / `nbo` sesuai harapan?** — 34/34, 64/64, atau 98/64
- [ ] **Audio tidak hilang?** — passthrough aktif
- [ ] **Musik nyasar?** — cek offset passthrough (mode MAIN pakai +34)

---

## 13. Contoh Kode Minimal (Copy-Paste)

### Script Test Callback

```python
"""
Minimal test — verify callback bekerja.
Jalankan: python test.py
"""
import ctypes
import logging
import time
from ctypes import c_long, c_float, c_void_p, c_char_p, POINTER, WINFUNCTYPE

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger('test')

# Constants
CB_STARTING = 0x01
CB_ENDING   = 0x02
CB_CHANGE   = 0x03
CB_IN       = 0x0A
CB_OUT      = 0x0B
CB_MAIN     = 0x14

MODE_IN   = 1
MODE_OUT  = 2
MODE_MAIN = 4

# Signature
CALLBACK_TYPE = WINFUNCTYPE(c_long, c_void_p, c_long, c_void_p, c_long)

def callback(lpUser, nCommand, lpData, nnn):
    if nCommand == CB_STARTING:
        log.info("▶️  STARTING")
    elif nCommand == CB_ENDING:
        log.info("⏹️  ENDING")
    elif nCommand == CB_CHANGE:
        log.info("🔄 CHANGE")
    elif nCommand in (CB_IN, CB_OUT, CB_MAIN):
        # Just count — no processing yet
        pass
    return 0

def main():
    dll = ctypes.WinDLL(r"C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll")
    dll.VBVMR_Login.restype = c_long
    dll.VBVMR_AudioCallbackRegister.restype = c_long
    dll.VBVMR_AudioCallbackRegister.argtypes = [c_long, CALLBACK_TYPE, c_void_p, c_char_p]
    dll.VBVMR_AudioCallbackStart.restype = c_long
    dll.VBVMR_AudioCallbackStop.restype = c_long
    dll.VBVMR_AudioCallbackUnregister.restype = c_long
    dll.VBVMR_Logout.restype = c_long

    # Login
    if dll.VBVMR_Login() < 0:
        log.error("Login failed")
        return 1
    log.info("✅ Login OK")

    # Register mode MAIN (bit flag 4)
    cb_ref = CALLBACK_TYPE(callback)
    ret = dll.VBVMR_AudioCallbackRegister(MODE_MAIN, cb_ref, None, b"S34-Test")
    if ret != 0:
        log.error(f"Register failed: {ret}")
        dll.VBVMR_Logout()
        return 1
    log.info("✅ Register OK")

    # Start
    if dll.VBVMR_AudioCallbackStart() != 0:
        log.error("Start failed")
        dll.VBVMR_AudioCallbackUnregister()
        dll.VBVMR_Logout()
        return 1
    log.info("✅ Start OK")

    # Wait
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    # Cleanup
    dll.VBVMR_AudioCallbackStop()
    dll.VBVMR_AudioCallbackUnregister()
    dll.VBVMR_Logout()
    log.info("Done")

if __name__ == "__main__":
    main()
```

---

## 14. Referensi SDK & Sumber Belajar

### File SDK Resmi

Kalau Voicemeeter terinstall, biasanya file tersedia di:
```
C:\Program Files (x86)\VB\Voicemeeter\
├── VoicemeeterRemote64.dll
├── VoicemeeterRemote.dll
└── (mungkin) VoicemeeterRemote.h
```

### File Header C (Rust Bindings)

Digunakan dalam proyek ini (tested):
- `VoicemeeterRemote.h` — Header C dengan semua konstanta & struct
- File bindings Rust (auto-generated) — mirror dari header, dengan komentar

### Contoh Kode Resmi

- **`vmr_client.c`** — Contoh lengkap Win32 client
  - Login/logout
  - GetParameter / SetParameter
  - GetLevel (meter)
  - MIDI in/out
  - **Audio Callback** (semua mode!)
  - Macro Buttons
  - Custom Button

- **`vmr_matrix.c`** — Contoh APO (Audio Processing Object)
  - 8×8 gain matrix
  - Audio callback mode OUT
  - Selector bus
  - **Pola passthrough + process** yang benar

### Komunitas & Referensi Online

- **VB-Audio Forum**: https://forum.vb-audio.com/
- **GitHub `vburel2018/Voicemeeter-SDK`**: SDK resmi
- **Python wrapper** (tidak support callback): `onyx-and-iris/voicemeeter-api-python`
- **Rust crate**: `voicemeeter` di crates.io (support callback!)
- **C# example**: `A-tG/Voicemeeter-AudioCallback-Simple-Example`

### Proyek yang Pakai Callback

- **Equalizer APO** — Pakai callback untuk process audio
- **Voicemeeter MacroButtons** — Pakai callback untuk macro triggers
- **Swara 34** — Proyek kita! 🚀

---

## 📝 Changelog

| Tanggal | Versi | Perubahan |
|---|---|---|
| 2026-10-14 | 1.0 | Initial release — verified di Voicemeeter 3.1.3.0 |
| — | — | (Tambahkan entri kalau ada update) |

---

## 📜 Lisensi & Atribusi

- Dokumen ini bebas dipakai (CC0 / Public Domain)
- Voicemeeter Remote API © Vincent Burel / VB-Audio Software
- SDK example (`vmr_client.c`, `vmr_matrix.c`) © V.Burel, 2015-2026
- Penggunaan API untuk aplikasi komersial diizinkan sejak Maret 2021
- **Bukan afiliasi resmi dengan VB-Audio**

---

## ⚡ TL;DR — 5 Poin Kunci

1. **Mode callback = BIT FLAG**, bukan sequential: `IN=1, OUT=2, MAIN=4`
2. **Command values**: `STARTING=0x01, ENDING=0x02, CHANGE=0x03, BUFFER_IN=0x0A, BUFFER_OUT=0x0B, BUFFER_MAIN=0x14`
3. **Mode MAIN**: `nbi=98` (34 strip + 64 bus), `nbo=64`. **Passthrough pakai offset +34!**
4. **Signature callback 4 argumen**: `(lpUser, nCommand, lpData, nnn)`, pakai `WINFUNCTYPE`
5. **Selalu auto-passthrough** (copy input → output) supaya audio tidak hilang, lalu jalankan DSP.

---

*Generated by Swara 34 project — 2026-10-14*