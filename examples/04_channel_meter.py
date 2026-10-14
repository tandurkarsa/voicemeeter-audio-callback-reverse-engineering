"""
04_channel_meter.py — Real-time level meter for all 34 channels.

Registers MAIN callback + reads peak levels of all input channels.
Displays live meter in terminal.

This is the foundation for building a mixer UI — you need to know
what each channel's level is, in real-time.

Usage:
    python 04_channel_meter.py

Expected: live bars showing each strip's level (34 bars).
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
# Enable ANSI escape codes on Windows terminal
import os
if sys.platform == 'win32':
    os.system('')  # side-effect: enables VT100 in cmd.exe/PowerShell

import signal

# ─── Graceful exit flag ───
_running = [True]

def _signal_handler(sig, frame):
    """Ctrl+C handler — set flag, exit loop gracefully."""
    _running[0] = False

# Register di Windows (SIGINT = Ctrl+C)
signal.signal(signal.SIGINT, _signal_handler)

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('meter')

DLL_PATHS = [
    r"C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll",
    r"C:\Program Files\VB\Voicemeeter\VoicemeeterRemote64.dll",
]

CALLBACK_TYPE = WINFUNCTYPE(c_long, c_void_p, c_long, c_void_p, c_long)

FloatPtrArray = POINTER(c_float) * 128


class VBVMR_AUDIOBUFFER(Structure):
    _fields_ = [
        ("sr",  c_long), ("nbs", c_long),
        ("nbi", c_long), ("nbo", c_long),
        ("r",   FloatPtrArray), ("w",   FloatPtrArray),
    ]


def ptr_to_numpy(ptr, n):
    if not ptr:
        return None
    BufType = c_float * n
    return np.ctypeslib.as_array(
        ctypes.cast(ptr, POINTER(BufType)).contents)


# Channel names for Potato (34 channels)
CHANNEL_NAMES = [
    "HW1.L", "HW1.R", "HW2.L", "HW2.R", "HW3.L", "HW3.R",
    "HW4.L", "HW4.R", "HW5.L", "HW5.R",
    "VAIO.FL", "VAIO.FR", "VAIO.C", "VAIO.LFE",
    "VAIO.RL", "VAIO.RR", "VAIO.SL", "VAIO.SR",
    "AUX.FL", "AUX.FR", "AUX.C", "AUX.LFE",
    "AUX.RL", "AUX.RR", "AUX.SL", "AUX.SR",
    "VAIO3.FL", "VAIO3.FR", "VAIO3.C", "VAIO3.LFE",
    "VAIO3.RL", "VAIO3.RR", "VAIO3.SL", "VAIO3.SR",
]

# Shared peak levels (atomic-ish float writes are fine for display)
levels = np.zeros(34, dtype=np.float32)
peak_hold = np.zeros(34, dtype=np.float32)
call_count = [0]


def callback(lpUser, nCommand, lpData, nnn):
    if nCommand != 0x14 or not lpData:
        return 0

    call_count[0] += 1
    raw = ctypes.cast(lpData, POINTER(VBVMR_AUDIOBUFFER)).contents
    nbs = int(raw.nbs)
    nbi = int(raw.nbi)
    n_strips = min(nbi, 34)

    # Read peak per strip channel
    for i in range(n_strips):
        ptr = raw.r[i]
        if not ptr:
            continue
        arr = ptr_to_numpy(ptr, nbs)
        if arr is None:
            continue
        peak = float(np.max(np.abs(arr)))
        if peak > levels[i]:
            levels[i] = peak
        # Peak hold with decay
        if peak > peak_hold[i]:
            peak_hold[i] = peak

    # Passthrough (so audio doesn't disappear)
    n_strips_total = nbi - int(raw.nbo)
    for i in range(int(raw.nbo)):
        src_ptr = raw.r[n_strips_total + i]
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


def render_meter():
    """Render ASCII meters in terminal."""
    # ANSI clear screen
    # Clear screen + move home + hide cursor (biar flicker minimal)
    print("\033[?25l\033[2J\033[H", end="")

    print("═" * 78)
    print(f"  Voicemeeter Channel Meter — callbacks: {call_count[0]}")
    print("═" * 78)
    print()

    for i in range(34):
        name = CHANNEL_NAMES[i]
        lvl = float(levels[i])
        hold = float(peak_hold[i])

        # Convert to dB
        if lvl > 1e-6:
            db = 20 * np.log10(lvl)
        else:
            db = -80.0

        # Bar: -60 dB .. 0 dB → 0 .. 50 chars
        bar_len = max(0, int((db + 60) / 60 * 50))
        bar_len = min(bar_len, 50)

        # Color
        if db > -3:
            color = "\033[91m"  # red
        elif db > -12:
            color = "\033[93m"  # yellow
        else:
            color = "\033[92m"  # green

        bar = "█" * bar_len + "░" * (50 - bar_len)
        marker = "▌" if hold > 0.001 else " "

        print(f"  {i+1:>2} {name:<10} "
              f"{color}{bar}\033[0m{marker} {db:>6.1f} dB")

    print()
    print("Press Ctrl+C to exit")
    print("═" * 78)


def main():
    print("Voicemeeter Channel Meter")
    print("=" * 40)

    dll_path = find_dll()
    if not dll_path:
        print("DLL not found")
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
        print("Login failed")
        return 1
    print("Login OK. Starting in 2 seconds...")
    time.sleep(2)

    cb_ref = CALLBACK_TYPE(callback)
    ret = dll.VBVMR_AudioCallbackRegister(
        4, cb_ref, None, b"S34-Meter")
    if ret != 0:
        print(f"Register failed: {ret}")
        dll.VBVMR_Logout()
        return 1
    if dll.VBVMR_AudioCallbackStart() != 0:
        print("Start failed")
        dll.VBVMR_AudioCallbackUnregister()
        dll.VBVMR_Logout()
        return 1

    try:
        while _running[0]:
            render_meter()
            levels[:] *= 0.7
            peak_hold[:] *= 0.95
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        # ═══ Reset terminal ANSI state ═══
        print("\033[0m\033[?25h", end="")   # Reset attributes + show cursor
        print()                             # Newline
        print("Stopping...")

        # ─── Cleanup ───
        try:
            dll.VBVMR_AudioCallbackStop()
        except Exception as e:
            print(f"Stop warning: {e}")
        try:
            dll.VBVMR_AudioCallbackUnregister()
        except Exception as e:
            print(f"Unregister warning: {e}")
        try:
            dll.VBVMR_Logout()
        except Exception as e:
            print(f"Logout warning: {e}")

        print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
