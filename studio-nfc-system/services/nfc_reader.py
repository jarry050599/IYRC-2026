#!/usr/bin/env python3
"""PN532 NFC reader daemon. Use --simulate to type UIDs without hardware."""
import argparse
import logging
import time

import requests


def normalize(uid: str) -> str:
    return uid.strip().upper().replace(":", "").replace("-", "")


def post_uid(api_url: str, uid: str):
    try:
        response = requests.post(f"{api_url.rstrip('/')}/api/nfc/tap",
                                 json={"card_uid": normalize(uid)}, timeout=5)
        payload = response.json()
        logging.info("tap %s: %s", uid, payload.get("message", payload))
    except requests.RequestException as exc:
        logging.error("API unavailable: %s", exc)


def simulate(api_url: str):
    print("NFC 模擬模式。輸入卡片 UID 後按 Enter，Ctrl+C 結束。")
    while True:
        uid = input("UID> ").strip()
        if uid:
            post_uid(api_url, uid)


def hardware(api_url: str, device: str):
    try:
        import nfc
    except ImportError as exc:
        raise SystemExit("尚未安裝 nfcpy，請執行 pip install -r requirements-nfc.txt") from exc
    while True:
        try:
            with nfc.ContactlessFrontend(device) as clf:
                logging.info("NFC reader ready on %s", device)
                clf.connect(rdwr={"on-connect": lambda tag: on_connect(tag, api_url)})
        except Exception as exc:
            logging.error("reader error: %s; retrying", exc)
            time.sleep(2)


def on_connect(tag, api_url: str):
    uid = getattr(tag, "identifier", b"").hex().upper()
    if uid:
        post_uid(api_url, uid)
    time.sleep(1)  # prevent repeated reads while the card remains on the reader
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true", help="鍵盤輸入 UID 模擬讀卡")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--device", default="usb", help="nfcpy device，例如 usb 或 tty:S0:pn532")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        simulate(args.api_url) if args.simulate else hardware(args.api_url, args.device)
    except KeyboardInterrupt:
        pass

