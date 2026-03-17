import socket
import requests
import sys
import os
import ssl
import yt_dlp

# Bypass SSL verification issues often found in data-center environments
ssl._create_default_https_context = ssl._create_unverified_context

# Monkeypatch socket.getaddrinfo to use Cloudflare DoH
# This bypasses the system DNS block completely for yt-dlp
original_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host and not host.startswith('127.') and host != 'localhost':
        try:
            # Using Cloudflare DoH to resolve the IP
            r = requests.get(
                f"https://cloudflare-dns.com/dns-query?name={host}&type=A", 
                headers={"Accept": "application/dns-json"},
                timeout=3
            )
            data = r.json()
            if "Answer" in data:
                ips = [record["data"] for record in data["Answer"] if record["type"] == 1]
                if ips:
                    # Return the resolved IP
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ips[0], port))]
        except Exception:
            pass # Fallback to system DNS if DoH fails
            
    return original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = custom_getaddrinfo

if __name__ == "__main__":
    # Clean arguments to prevent yt-dlp option errors
    args = [a for a in sys.argv if "--dns-over-https" not in a]
    sys.argv = args
    yt_dlp.main()
