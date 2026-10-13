#!/usr/bin/env python3
"""
show_key.py -- safely inspect your Roblox Open Cloud API key file.

Prints the FORMAT of the key (length, charset, whether it is base64, whether it
decodes) WITHOUT revealing the secret, so you can confirm you copied it right.

KEY FACT: for Roblox the base64 text IS the credential. You send it to the
`x-api-key` header EXACTLY as it is. You do NOT decode it. (Decoding only shows
the raw binary bytes underneath, which are not human-readable.)

Usage:
    python scripts/show_key.py
    python scripts/show_key.py --file "C:\\path\\to\\key.txt"
    python scripts/show_key.py --show          # also print a MASKED preview
"""

import argparse
import base64
import os
import re
import sys

try:
    import config
    DEFAULT_FILE = config.API_KEY_FILE
except Exception:
    DEFAULT_FILE = None


def main() -> None:
    ap = argparse.ArgumentParser(description="Inspect an Open Cloud key file (safely).")
    ap.add_argument("--file", default=DEFAULT_FILE, help="path to the key file")
    ap.add_argument("--show", action="store_true", help="print a MASKED preview (first/last 4 chars)")
    a = ap.parse_args()

    if not a.file:
        sys.exit("No key file given. Use --file PATH, or set API_KEY_FILE in config.py")

    if not os.path.exists(a.file):
        sys.exit(f"File not found: {a.file}")

    text = open(a.file, encoding="utf-8").read()
    raw = text.strip()
    line_count = len([l for l in text.splitlines() if l.strip()])

    print("Open Cloud key check")
    print("--------------------")
    print(f"file            : {a.file}")
    print(f"key length      : {len(raw)}")
    print(f"non-empty lines : {line_count}   (should be 1)")
    print(f"contains spaces : {any(c.isspace() for c in raw)}")
    print(f"multiple of 4   : {len(raw) % 4 == 0}")
    print(f"ends with '='   : {raw.endswith('=')}")
    print(f"base64 charset  : {bool(re.fullmatch(r'[A-Za-z0-9+/=]+', raw))}")

    try:
        decoded = base64.b64decode(raw, validate=True)
        printable = all(32 <= b < 127 for b in decoded)
        print(f"base64 decodes  : yes ({len(decoded)} bytes)")
        print(f"decoded is text : {printable}")
    except Exception as e:
        print(f"base64 decodes  : no ({e})")

    if a.show:
        if len(raw) > 12:
            print(f"masked preview  : {raw[:4]}...{raw[-4:]}")
        else:
            print("masked preview  : (key too short)")

    print()
    print("Reminder")
    print("--------")
    print("For Roblox you do NOT decode the key. Send it EXACTLY as-is in the")
    print("`x-api-key` header. The base64 text IS the credential.")


if __name__ == "__main__":
    main()
