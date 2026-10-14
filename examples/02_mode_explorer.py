"""
02_mode_explorer.py — Discover which mode does what.

Tests each callback mode sequentially:
    0  → expected INVALID
    1  → expected INPUT INSERT
    2  → expected OUTPUT INSERT
    4  → expected MAIN (all I/O)
    7  → expected ALL streams

For each mode, logs commands received and channel counts.
This is how you VERIFY what Voicemeeter does on your system.

Usage:
    python 02_mode_explorer.py

Expected (Potato 3.1.3.0):
    Mode 0: ❌ ret=-100
    Mode 1: ✅ cmd=0x0A  nbi=34  nbo=34
    Mode 2: ✅ cmd=0x0B  nbi=64  nbo=64
    Mode 4: ✅ cmd=0x14  nbi=98  nbo=64   ⭐
    Mode 7: ✅ cmd=0x0A,0x0B,0x14
"""
import ctypes
import logging
import os
import sys
import time
from ctypes import c_long, c_void_p, c_char_p, WINFUNCTYPE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('explorer')

CMD_NAMES = {
    0x01: "STARTING", 0x02: "ENDING", 0x03: "CHANGE",
    0x0A: "BUFFER_IN", 0x0B: "BUFFER_OUT", 0x14: "BUFFER_MAIN",
}

DLL_PATHS = [
    r"C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll",
    r"C:\Program Files\VB\Voicemeeter\VoicemeeterRemote64.dll",
]

CALLBACK_TYPE = WINFUNCTYPE(c_long, c_void_p, c_long, c_void_p, c_long)


class BufferHead(ctypes.Structure):
    _fields_ = [
        ("sr", ctypes.c_long), ("nbs", ctypes.c_long),
        ("nbi", ctypes.c_long), ("nbo", ctypes.c_long),
    ]

class BufferFull(ctypes.Structure):
    _fields_ = [
        ("sr",  ctypes.c_long), ("nbs", ctypes.c_long),
        ("nbi", ctypes.c_long), ("nbo", ctypes.c_long),
        ("r",   ctypes.POINTER(ctypes.c_float) * 128),
        ("w",   ctypes.POINTER(ctypes.c_float) * 128),
    ]


# Global stats per test
current_stats = {"cmds": {}, "buffer": None}


def callback(lpUser, nCommand, lpData, nnn):
    """Callback — logs command + passthrough audio."""
    name = CMD_NAMES.get(nCommand, f"UNKNOWN_0x{nCommand:X}")
    current_stats["cmds"][name] = current_stats["cmds"].get(name, 0) + 1

    if not lpData:
        return 0
    if nCommand not in (0x0A, 0x0B, 0x14):
        return 0

    # Parse buffer
    raw = ctypes.cast(lpData, ctypes.POINTER(BufferHead)).contents
    if current_stats["buffer"] is None:
        current_stats["buffer"] = (raw.sr, raw.nbs, raw.nbi, raw.nbo)

    # ─── PASSTHROUGH (so music keeps playing) ───
    class BufFull(ctypes.Structure):
        _fields_ = [
            ("sr",  ctypes.c_long), ("nbs", ctypes.c_long),
            ("nbi", ctypes.c_long), ("nbo", ctypes.c_long),
            ("r",   ctypes.POINTER(ctypes.c_float) * 128),
            ("w",   ctypes.POINTER(ctypes.c_float) * 128),
        ]
    full = ctypes.cast(lpData, ctypes.POINTER(BufFull)).contents
    nbs, nbi, nbo = int(full.nbs), int(full.nbi), int(full.nbo)

    if nCommand == 0x14:  # MAIN
        n_strips = nbi - nbo
        for i in range(nbo):
            s, d = full.r[n_strips + i], full.w[i]
            if s and d:
                ctypes.memmove(d, s, nbs * 4)
    else:
        for i in range(min(nbi, nbo)):
            s, d = full.r[i], full.w[i]
            if s and d:
                ctypes.memmove(d, s, nbs * 4)

    return 0


def find_dll():
    for p in DLL_PATHS:
        if os.path.isfile(p):
            return p
    return None


def test_mode(dll, mode, duration=4.0):
    """Test one mode. Returns dict with result."""
    global current_stats
    current_stats = {"cmds": {}, "buffer": None}

    log.info(f"\n{'─' * 60}")
    log.info(f"  TESTING MODE: {mode}  ({bin(mode)})")
    log.info(f"{'─' * 60}")

    cb_ref = CALLBACK_TYPE(callback)
    ret = dll.VBVMR_AudioCallbackRegister(
        mode, cb_ref, None, f"S34-Explorer-{mode}".encode())

    if ret != 0:
        log.warning(f"  Register failed: ret={ret}")
        return {"ok": False, "ret": ret}

    ret = dll.VBVMR_AudioCallbackStart()
    if ret != 0:
        log.warning(f"  Start failed: ret={ret}")
        dll.VBVMR_AudioCallbackUnregister()
        return {"ok": False, "ret": ret}

    log.info(f"  Active — observing for {duration}s...")
    t0 = time.time()
    while time.time() - t0 < duration:
        time.sleep(0.5)

    dll.VBVMR_AudioCallbackStop()
    dll.VBVMR_AudioCallbackUnregister()

    result = {
        "ok": True,
        "cmds": dict(current_stats["cmds"]),
        "buffer": current_stats["buffer"],
    }
    return result


def main():
    log.info("=" * 60)
    log.info("  Voicemeeter Audio Callback — Mode Explorer")
    log.info("=" * 60)

    dll_path = find_dll()
    if not dll_path:
        log.error("DLL not found")
        return 1

    dll = ctypes.WinDLL(dll_path)
    dll.VBVMR_Login.restype = c_long
    dll.VBVMR_Logout.restype = c_long
    dll.VBVMR_AudioCallbackRegister.restype = c_long
    dll.VBVMR_AudioCallbackRegister.argtypes = [
        c_long, CALLBACK_TYPE, c_void_p, c_char_p]
    dll.VBVMR_AudioCallbackStart.restype = c_long
    dll.VBVMR_AudioCallbackStart.argtypes = []
    dll.VBVMR_AudioCallbackStop.restype = c_long
    dll.VBVMR_AudioCallbackStop.argtypes = []
    dll.VBVMR_AudioCallbackUnregister.restype = c_long
    dll.VBVMR_AudioCallbackUnregister.argtypes = []

    if dll.VBVMR_Login() < 0:
        log.error("Login failed")
        return 1
    log.info("Login OK")

    log.info("")
    log.info("⚠️  MAKE SURE MUSIC IS PLAYING!")
    log.info("   Starting in 5 seconds...")
    for i in range(5, 0, -1):
        log.info(f"   {i}...")
        time.sleep(1)

    results = {}
    for mode in [0, 1, 2, 4, 7]:
        results[mode] = test_mode(dll, mode, duration=4.0)

    # Summary
    log.info("\n" + "=" * 60)
    log.info("  SUMMARY")
    log.info("=" * 60)

    expected_invalid = {0}   # Mode 0 = expected to fail
    for mode, r in results.items():
        label = f"Mode {mode} ({bin(mode):>5})"
        if not r.get("ok"):
            if mode in expected_invalid:
                log.info(f"  {label}: ⚠️  ret={r.get('ret')}  (EXPECTED — mode 0 invalid)")
            else:
                log.info(f"  {label}: ❌ ret={r.get('ret')}")
        else:
            cmds = ", ".join(f"{k}={v}" for k, v in r["cmds"].items())
            buf = r["buffer"]
            buf_str = (f"sr={buf[0]} nbs={buf[1]} nbi={buf[2]} nbo={buf[3]}"
                       if buf else "no buffer")
            log.info(f"  {label}: ✅ {cmds}")
            log.info(f"                {buf_str}")

    log.info("")
    log.info("  Expected mapping (Potato 3.1.3.0):")
    log.info("    Mode 0 → ❌ invalid")
    log.info("    Mode 1 → IN  (0x0A, nbi=34)")
    log.info("    Mode 2 → OUT (0x0B, nbi=64)")
    log.info("    Mode 4 → MAIN (0x14, nbi=98 nbo=64)  ⭐")
    log.info("    Mode 7 → ALL")

    dll.VBVMR_Logout()
    return 0


if __name__ == "__main__":
    sys.exit(main())
