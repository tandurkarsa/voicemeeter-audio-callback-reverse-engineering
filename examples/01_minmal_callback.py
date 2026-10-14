"""
01_minimal_callback.py — Hello World Voicemeeter Audio Callback.

Registers a callback in MAIN mode (bit flag 4) and logs every command.

Requirements:
    - Voicemeeter Potato/Banana/Basic running
    - Audio actively playing through Voicemeeter
    - Python 3.8+, numpy
    - VoicemeeterRemote64.dll

Usage:
    python 01_minimal_callback.py

Expected output (with music playing):
    [INFO] Login OK
    [INFO] Register OK (mode=MAIN=4)
    [INFO] Start OK
    [INFO] >>> STARTING
    [INFO] Buffer: sr=48000 nbs=2048 nbi=98 nbo=64
    [INFO] >>> BUFFER_MAIN count=50
    ...
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
log = logging.getLogger('minimal')

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════
CB_STARTING     = 0x01
CB_ENDING       = 0x02
CB_CHANGE       = 0x03
CB_BUFFER_IN    = 0x0A
CB_BUFFER_OUT   = 0x0B
CB_BUFFER_MAIN  = 0x14

# Mode bit flags (⚠️ NOT sequential!)
MODE_IN   = 1
MODE_OUT  = 2
MODE_MAIN = 4
MODE_ALL  = 7

CMD_NAMES = {
    CB_STARTING:    "STARTING",
    CB_ENDING:      "ENDING",
    CB_CHANGE:      "CHANGE",
    CB_BUFFER_IN:   "BUFFER_IN",
    CB_BUFFER_OUT:  "BUFFER_OUT",
    CB_BUFFER_MAIN: "BUFFER_MAIN",
}

DLL_PATHS = [
    r"C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll",
    r"C:\Program Files\VB\Voicemeeter\VoicemeeterRemote64.dll",
]

# 4-arg callback signature (⚠️ 2-arg version gives nCommand=0!)
CALLBACK_TYPE = WINFUNCTYPE(c_long, c_void_p, c_long, c_void_p, c_long)

# ═══════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════════
counter = {}
first_buffer_logged = False


def callback(lpUser, nCommand, lpData, nnn):
    """Callback handler — called from Voicemeeter's real-time thread."""
    global first_buffer_logged

    name = CMD_NAMES.get(nCommand, f"UNKNOWN_0x{nCommand:X}")
    counter[name] = counter.get(name, 0) + 1

    if nCommand == CB_STARTING:
        log.info(">>> STARTING (init DSP here)")
    elif nCommand == CB_ENDING:
        log.info(">>> ENDING (cleanup DSP here)")
    elif nCommand == CB_CHANGE:
        log.info(">>> CHANGE (samplerate/buffer changed)")
    elif nCommand in (CB_BUFFER_IN, CB_BUFFER_OUT, CB_BUFFER_MAIN):
        # Log first buffer info
        if not first_buffer_logged and lpData:
            class BufHead(ctypes.Structure):
                _fields_ = [
                    ("sr",  ctypes.c_long),
                    ("nbs", ctypes.c_long),
                    ("nbi", ctypes.c_long),
                    ("nbo", ctypes.c_long),
                ]
            h = ctypes.cast(lpData, ctypes.POINTER(BufHead)).contents
            log.info(f"Buffer: sr={h.sr} nbs={h.nbs} "
                     f"nbi={h.nbi} nbo={h.nbo}")
            first_buffer_logged = True

        # ─── MINIMAL PASSTHROUGH ───
        # Copy input → output so audio keeps playing.
        # For mode MAIN, bus read is at offset +n_strips.
        if lpData:
            class BufFull(ctypes.Structure):
                _fields_ = [
                    ("sr",  ctypes.c_long), ("nbs", ctypes.c_long),
                    ("nbi", ctypes.c_long), ("nbo", ctypes.c_long),
                    ("r",   ctypes.POINTER(ctypes.c_float) * 128),
                    ("w",   ctypes.POINTER(ctypes.c_float) * 128),
                ]
            raw = ctypes.cast(lpData, ctypes.POINTER(BufFull)).contents
            nbs, nbi, nbo = int(raw.nbs), int(raw.nbi), int(raw.nbo)
            FloatArr = ctypes.c_float * nbs

            if nCommand == CB_BUFFER_MAIN:
                # MAIN: nbi = strips + buses, nbo = buses
                n_strips = nbi - nbo
                for i in range(nbo):
                    src_ptr = raw.r[n_strips + i]
                    dst_ptr = raw.w[i]
                    if src_ptr and dst_ptr:
                        ctypes.memmove(dst_ptr, src_ptr,
                                        nbs * ctypes.sizeof(ctypes.c_float))
            else:
                # IN / OUT: 1:1
                n = min(nbi, nbo)
                for i in range(n):
                    src_ptr = raw.r[i]
                    dst_ptr = raw.w[i]
                    if src_ptr and dst_ptr:
                        ctypes.memmove(dst_ptr, src_ptr,
                                        nbs * ctypes.sizeof(ctypes.c_float))

    return 0


def find_dll():
    for p in DLL_PATHS:
        if os.path.isfile(p):
            return p
    return None


def main():
    log.info("=" * 60)
    log.info("  Minimal Voicemeeter Audio Callback Test")
    log.info("=" * 60)

    # Find DLL
    dll_path = find_dll()
    if not dll_path:
        log.error("VoicemeeterRemote64.dll not found!")
        log.error("Make sure Voicemeeter is installed.")
        return 1
    log.info(f"DLL: {dll_path}")

    # Load DLL
    try:
        dll = ctypes.WinDLL(dll_path)
    except OSError as e:
        log.error(f"Failed to load DLL: {e}")
        return 1

    # Setup prototypes
    dll.VBVMR_Login.restype = c_long
    dll.VBVMR_Login.argtypes = []
    dll.VBVMR_Logout.restype = c_long
    dll.VBVMR_Logout.argtypes = []
    dll.VBVMR_AudioCallbackRegister.restype = c_long
    dll.VBVMR_AudioCallbackRegister.argtypes = [
        c_long, CALLBACK_TYPE, c_void_p, c_char_p]
    dll.VBVMR_AudioCallbackStart.restype = c_long
    dll.VBVMR_AudioCallbackStart.argtypes = []
    dll.VBVMR_AudioCallbackStop.restype = c_long
    dll.VBVMR_AudioCallbackStop.argtypes = []
    dll.VBVMR_AudioCallbackUnregister.restype = c_long
    dll.VBVMR_AudioCallbackUnregister.argtypes = []

    # Login
    ret = dll.VBVMR_Login()
    if ret < 0:
        log.error(f"Login failed: {ret}")
        return 1
    log.info(f"Login OK (ret={ret})")

    # Register callback — MODE_MAIN = 4 (BIT FLAG!)
    cb_ref = CALLBACK_TYPE(callback)
    ret = dll.VBVMR_AudioCallbackRegister(
        MODE_MAIN, cb_ref, None, b"S34-Minimal")
    if ret != 0:
        log.error(f"Register failed: {ret}")
        log.error("  ret=1  → already registered by another app")
        log.error("  ret=-100 → callback slot full")
        dll.VBVMR_Logout()
        return 1
    log.info("Register OK (mode=MAIN=4)")

    # Start
    ret = dll.VBVMR_AudioCallbackStart()
    if ret != 0:
        log.error(f"Start failed: {ret}")
        dll.VBVMR_AudioCallbackUnregister()
        dll.VBVMR_Logout()
        return 1
    log.info("Start OK")
    log.info("")
    log.info(">>> PLAY MUSIC NOW! <<<")
    log.info("Watch for callback counts below.")
    log.info("Press Ctrl+C to stop.")
    log.info("")

    # Wait
    try:
        while True:
            time.sleep(3)
            log.info(f"Stats: {counter}")
    except KeyboardInterrupt:
        print()

    # Cleanup
    log.info("")
    log.info("Cleaning up...")
    dll.VBVMR_AudioCallbackStop()
    dll.VBVMR_AudioCallbackUnregister()
    dll.VBVMR_Logout()

    log.info(f"Final stats: {counter}")

    if counter.get("BUFFER_MAIN", 0) > 0:
        log.info("✅ SUCCESS — callback received BUFFER_MAIN data!")
    else:
        log.warning("⚠️ No BUFFER_MAIN — is music playing through Voicemeeter?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
