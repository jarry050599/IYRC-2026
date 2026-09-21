"""Generate a self-signed certificate so the admin UI can be served over HTTPS.

Browsers only expose the camera (QR scanning) on localhost or HTTPS, so reaching
the admin UI from a phone over the LAN needs TLS. This writes a certificate
covering the addresses you pass in; each device trusts it once, by hand.
"""

from __future__ import annotations

import argparse
import ipaddress
import socket
import subprocess
from pathlib import Path


def local_ip() -> str | None:
    """Best-effort LAN address: the source IP the kernel would route out with."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("192.0.2.1", 9))  # TEST-NET-1, no packet is sent
            return probe.getsockname()[0]
        except OSError:
            return None


def subject_alt_names(hosts: list[str]) -> str:
    names, index_dns, index_ip = [], 0, 0
    for host in dict.fromkeys(hosts):
        try:
            ipaddress.ip_address(host)
        except ValueError:
            index_dns += 1
            names.append(f"DNS.{index_dns}:{host}")
        else:
            index_ip += 1
            names.append(f"IP.{index_ip}:{host}")
    return ",".join(names)


def generate_cert(hosts: list[str], output_dir: Path, days: int) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cert, key = output_dir / "cert.pem", output_dir / "key.pem"
    alt_names = subject_alt_names(hosts)
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", str(key), "-out", str(cert), "-days", str(days),
         "-subj", "/CN=studio-nfc", "-addext", f"subjectAltName={alt_names}"],
        check=True, capture_output=True)
    key.chmod(0o600)
    return cert, key


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", action="append", default=[], metavar="IP_OR_NAME",
                        help="address the browser will use; repeatable (default: this machine's LAN IP)")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--days", type=int, default=825)
    args = parser.parse_args()

    hosts = list(args.host)
    if not hosts:
        detected = local_ip()
        if not detected:
            raise SystemExit("無法自動偵測區網 IP，請用 --host 指定，例如 --host 192.168.1.50")
        hosts.append(detected)
        print(f"未指定 --host，使用偵測到的區網 IP：{detected}")
    hosts += ["localhost", "127.0.0.1"]

    try:
        cert, key = generate_cert(hosts, args.output_dir, args.days)
    except FileNotFoundError:
        raise SystemExit("找不到 openssl，請先安裝：sudo apt install -y openssl")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"openssl 產生憑證失敗：{exc.stderr.decode(errors='replace').strip()}")

    print(f"憑證：{cert}\n私鑰：{key}（權限 600，請勿提交到版控）")
    print("\n啟動 HTTPS：")
    print(f"  uvicorn app.main:app --host 0.0.0.0 --port 8443 \\\n"
          f"    --ssl-keyfile {key} --ssl-certfile {cert}")
    print(f"\n手機開 https://{hosts[0]}:8443/admin，第一次會跳憑證警告，"
          "選「進階 → 仍要前往」之後相機才能掃 QR。")
