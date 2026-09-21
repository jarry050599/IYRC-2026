#!/usr/bin/env python3
"""PN532 NFC reader daemon. Use --simulate to type UIDs without hardware."""
import argparse
import glob
import logging
import sys
import time

import requests


# A UID remains latched only while the card is physically in the RF field.
# There is no check-in/check-out cooldown: an explicit no-card response clears
# the latch immediately, while one continuously held card still emits one tap.
last_tap = {"uid": None}

# requests' verify argument: True for ordinary TLS, or the path to the
# self-signed certificate when the API is served over HTTPS with one.
api_verify = True


def normalize(uid: str) -> str:
    return uid.strip().upper().replace(":", "").replace("-", "")


def post_uid(api_url: str, uid: str):
    try:
        response = requests.post(f"{api_url.rstrip('/')}/api/nfc/tap",
                                 json={"card_uid": normalize(uid)}, timeout=5,
                                 verify=api_verify)
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
    if sys.platform == "darwin" and device.startswith("tty:usbserial"):
        serial_name = device.split(":", 2)[1]
        pattern = "/dev/cu.usbserial-*" if serial_name == "usbserial" else f"/dev/cu.{serial_name}"
        ports = sorted(glob.glob(pattern))
        if not ports:
            raise SystemExit(f"找不到串列裝置 {serial_name}")
        return pn532_serial(api_url, ports[-1])
    try:
        import nfc
    except ImportError as exc:
        raise SystemExit("尚未安裝 nfcpy，請執行 pip install -r requirements-nfc.txt") from exc
    while True:
        try:
            with nfc.ContactlessFrontend(device) as clf:
                logging.info("NFC reader ready on %s", device)
                while True:
                    seen = {"card": False}
                    deadline = time.monotonic() + 0.55

                    def detected(tag):
                        seen["card"] = True
                        return on_connect(tag, api_url)

                    clf.connect(rdwr={"on-connect": detected},
                                terminate=lambda: time.monotonic() >= deadline)
                    if seen["card"]:
                        continue
                    if last_tap["uid"] is not None:
                        logging.info("card removed; reader re-armed immediately")
                        last_tap["uid"] = None
        except Exception as exc:
            logging.error("reader error: %s; retrying", exc)
            time.sleep(2)


def pn532_frame(data: bytes) -> bytes:
    length = len(data)
    return b"\x00\x00\xff" + bytes((length, (-length) & 0xff)) + data + bytes(((-sum(data)) & 0xff, 0))


def pn532_payloads(raw: bytes):
    index = 0
    while True:
        index = raw.find(b"\x00\x00\xff", index)
        if index < 0 or index + 6 > len(raw):
            return
        length = raw[index + 3]
        if length == 0:
            index += 6
            continue
        start, end = index + 5, index + 5 + length
        if end + 1 > len(raw):
            return
        yield raw[start:end]
        index = end + 2


def pn532_exchange(port, command: bytes, timeout: float = 0.32,
                   wake: bool = False) -> list[bytes]:
    port.reset_input_buffer()
    port.write((b"\x00" * 20 if wake else b"") + pn532_frame(b"\xd4" + command))
    port.flush()
    deadline, raw = time.monotonic() + timeout, bytearray()
    while time.monotonic() < deadline:
        chunk = port.read(128)
        if chunk:
            raw.extend(chunk)
        else:
            time.sleep(0.01)
    return list(pn532_payloads(bytes(raw)))


def pn532_serial(api_url: str, port_name: str):
    import serial
    while True:
        try:
            # macOS may recreate a USB serial device after the adapter resets.
            # Resolve the current path on every reconnect instead of retaining
            # a stale device node.
            candidates = sorted(glob.glob("/dev/cu.usbserial-*"))
            current_port = port_name if port_name in candidates else (candidates[-1] if candidates else None)
            if not current_port:
                logging.warning("USB serial reader unavailable; waiting for reconnect")
                time.sleep(2)
                continue
            with serial.Serial(current_port, 115200, timeout=0.04) as port:
                # Wake once after opening. Sending the long wake preamble for
                # every poll can reset some USB-C/UART PN532 adapters.
                firmware = []
                for _ in range(3):
                    firmware = pn532_exchange(port, b"\x02", timeout=0.65, wake=True)
                    if any(payload[:2] == b"\xd5\x03" for payload in firmware):
                        break
                    time.sleep(0.15)
                if not any(payload[:2] == b"\xd5\x03" for payload in firmware):
                    raise RuntimeError("PN532 did not answer firmware query")
                sam = pn532_exchange(port, b"\x14\x01\x00\x00", timeout=0.7, wake=True)
                if not any(payload[:2] == b"\xd5\x15" for payload in sam):
                    raise RuntimeError("PN532 SAM configuration failed")
                # Cycle the RF field once per hardware connection. This
                # restores boards whose UART interface responds normally but
                # whose antenna field remained disabled after a USB reset.
                pn532_exchange(port, b"\x32\x01\x00", timeout=0.4, wake=True)
                time.sleep(0.08)
                pn532_exchange(port, b"\x32\x01\x01", timeout=0.4, wake=True)
                # Some UART PN532 boards acknowledge RFConfiguration but leave
                # CIU_TxControl at 0x00. Explicitly enable TX1/TX2 (0x83).
                write_rf = pn532_exchange(port, b"\x08\x63\x03\x83", timeout=0.7, wake=True)
                if not any(payload[:2] == b"\xd5\x09" for payload in write_rf):
                    raise RuntimeError("PN532 antenna enable failed")
                pn532_exchange(port, b"\x06\x63\x03", timeout=0.6)
                logging.info("NFC reader ready on %s (direct PN532 mode)", current_port)
                while True:
                    responses = pn532_exchange(port, b"\x4a\x01\x00", timeout=0.45)
                    uid = None
                    for payload in responses:
                        if len(payload) >= 3 and payload[:2] == b"\xd5\x4b":
                            if payload[2] > 0 and len(payload) >= 10:
                                uid_length = payload[7]
                                uid = payload[8:8 + uid_length].hex().upper()
                            break
                    if uid:
                        if uid != last_tap["uid"]:
                            post_uid(api_url, uid)
                            last_tap["uid"] = uid
                        # Release the selected target before the next poll. The
                        # UID latch still suppresses a held card, while a real
                        # removal can now be detected and re-armed quickly.
                        pn532_exchange(port, b"\x52\x01", timeout=0.25)
                    # Some UART PN532 firmware does not return a D5 4B packet
                    # when the RF field is empty; it simply times out. Treat
                    # that completed no-UID poll as the removal edge too.
                    elif last_tap["uid"] is not None:
                        logging.info("card removed; reader re-armed immediately")
                        last_tap["uid"] = None
                    time.sleep(0.05)
        except Exception as exc:
            logging.error("direct reader error: %s; retrying", exc)
            time.sleep(2)


def on_connect(tag, api_url: str):
    uid = getattr(tag, "identifier", b"").hex().upper()
    if uid and uid != last_tap["uid"]:
        post_uid(api_url, uid)
        last_tap["uid"] = uid
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true", help="鍵盤輸入 UID 模擬讀卡")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--device", default="usb", help="nfcpy device，例如 usb 或 tty:S0:pn532")
    parser.add_argument("--ca-cert", default=None, metavar="PATH",
                        help="API 走 HTTPS 自簽憑證時，指向 data/cert.pem 以便驗證")
    args = parser.parse_args()
    if args.ca_cert:
        api_verify = args.ca_cert
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        simulate(args.api_url) if args.simulate else hardware(args.api_url, args.device)
    except KeyboardInterrupt:
        pass
