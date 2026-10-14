"""
03_passthrough_audio.py — Fix the "audio disappears" problem.

When you register a callback, Voicemeeter expects YOU to write
output buffers. If you don't, audio disappears (silence).

This example shows how to AUTO-PASSTHROUGH — copy input → output
before running any DSP, so audio keeps playing normally.

KEY INSIGHT: Mode MAIN has different buffer layout:
    inputs[0..33]  = 34 strip channels
    inputs[34..97] = 64 bus channels
    outputs[0..63] = 64 bus channels
    ⚠️  Passthrough MUST use offset +34!

Usage:
    python 03_passthrough_audio.py

Expected: music keeps playing normally, no leaks to random channels.
"""
import ctypes
import logging
import os
import sys
import time
from ctypes import (
    c_long, c_float, c_void_p, c_char_p, POINTER, Structure, WINFUNCTYPE,
)
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('passthrough')

CMD_NAMES = {
    0x01: "STARTING", 0x02: "ENDING", 0x03: "CHANGE",
    0x0A: "BUFFER_IN", 0x0B: "BUFFER_OUT", 0x14: "BUFFER_MAIN",
}

DLL_PATHS = [
    r"C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll",
    r"C:\Program Files\VB\Voicemeeter\VoicemeeterRemote64.dll",
]

CALLBACK_TYPE = WINFUNCTYPE(c_long, c_void_p, c_long, c_void_p, c_long)

FloatPtrArray = POINTER(c_float) * 128


class VBVMR_AUDIOBUFFER(Structure):
    _fields_ = [
        ("sr",  c_long),
        ("nbs", c_long),
        ("nbi", c_long),
        ("nbo", c_long),
        ("r",   FloatPtrArray),
        ("w",   FloatPtrArray),
    ]


def ptr_to_numpy(ptr, n):
    if not ptr:
        return None
    BufType = c_float * n
    return np.ctypeslib.as_array(
        ctypes.cast(ptr, POINTER(BufType)).contents)


counter = {"calls": 0, "first_buffer_logged": False}


def callback(lpUser, nCommand, lpData, nnn):
    global counter

    if nCommand == 0x01:  # STARTING
        log.info(">>> STARTING")
        return 0
    if nCommand == 0x02:  # ENDING
        log.info(">>> ENDING")
        return 0
    if nCommand == 0x03:  # CHANGE
        log.info(">>> CHANGE")
        return 0

    if nCommand not in (0x0A, 0x0B, 0x14):
        return 0
    if not lpData:
        return 0

    counter["calls"] += 1

    # Parse buffer
    raw = ctypes.cast(lpData, POINTER(VBVMR_AUDIOBUFFER)).contents
    sr = int(raw.sr)
    nbs = int(raw.nbs)
    nbi = int(raw.nbi)
    nbo = int(raw.nbo)

    if not counter["first_buffer_logged"]:
        log.info(f"Buffer: sr={sr} nbs={nbs} nbi={nbi} nbo={nbo}")
        counter["first_buffer_logged"] = True

    # ═══════════════════════════════════════════════════════════════
    # AUTO-PASSTHROUGH
    # ═══════════════════════════════════════════════════════════════
    if nCommand == 0x14:  # MAIN mode
        # MAIN layout: nbi = 34 strips + 64 buses, nbo = 64 buses
        # Copy bus read (offset +34) → bus write
        n_strips = nbi - nbo  # = 34 when nbi=98, nbo=64
        for i in range(nbo):
            src_ptr = raw.r[n_strips + i]
            dst_ptr = raw.w[i]
            if src_ptr and dst_ptr:
                src = ptr_to_numpy(src_ptr, nbs)
                dst = ptr_to_numpy(dst_ptr, nbs)
                if src is not None and dst is not None:
                    dst[:] = src[:]
    else:
        # IN / OUT mode: copy 1:1
        n = min(nbi, nbo)
        for i in range(n):
            src_ptr = raw.r[i]
            dst_ptr = raw.w[i]
            if src_ptr and dst_ptr:
                src = ptr_to_numpy(src_ptr, nbs)
                dst = ptr_to_numpy(dst_ptr, nbs)
                if src is not None and dst is not None:
                    dst[:] = src[:]

    return 0


def find_dll():
    for p in DLL_PATHS:
        if os.path.isfile(p):
            return p
    return None


def main():
    log.info("=" * 60)
    log.info("  Passthrough Test — Music should keep playing")
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
    dll.VBVMR_AudioCallbackStop.restype = c_long
    dll.VBVMR_AudioCallbackUnregister.restype = c_long

    if dll.VBVMR_Login() < 0:
        log.error("Login failed")
        return 1
    log.info("Login OK")

    # Register mode MAIN = 4 (bit flag!)
    cb_ref = CALLBACK_TYPE(callback)
    ret = dll.VBVMR_AudioCallbackRegister(
        4, cb_ref, None, b"S34-Passthrough")
    if ret != 0:
        log.error(f"Register failed: {ret}")
        dll.VBVMR_Logout()
        return 1
    log.info("Register OK (mode=MAIN=4)")

    if dll.VBVMR_AudioCallbackStart() != 0:
        log.error("Start failed")
        dll.VBVMR_AudioCallbackUnregister()
        dll.VBVMR_Logout()
        return 1
    log.info("Start OK")
    log.info("")
    log.info(">>> MUSIC SHOULD STILL PLAY NORMALLY <<<")
    log.info("Press Ctrl+C to stop.")
    log.info("")

    try:
        while True:
            time.sleep(3)
            log.info(f"Callbacks: {counter['calls']}")
    except KeyboardInterrupt:
        print()

    log.info("")
    log.info("Cleanup...")
    dll.VBVMR_AudioCallbackStop()
    dll.VBVMR_AudioCallbackUnregister()
    dll.VBVMR_Logout()
    log.info(f"Total callbacks: {counter['calls']}")

    if counter["calls"] > 0:
        log.info("✅ Passthrough test complete!")
    else:
        log.warning("⚠️ No callbacks received")
    return 0


if __name__ == "__main__":
    sys.exit(main())