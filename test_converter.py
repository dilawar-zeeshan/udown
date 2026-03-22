raw_cookies = "ST-3o=xxx;__Secure-3PSID=yyy;SID=zzz"
netscape_lines = ["# Netscape HTTP Cookie File\n"]
import time
expire = int(time.time()) + 31536000
for pair in raw_cookies.split(";"):
    pair = pair.strip()
    if not pair or "=" not in pair: continue
    k, v = pair.split("=", 1)
    prefix = "#HttpOnly_.youtube.com" if k.startswith("__Secure") else ".youtube.com"
    netscape_lines.append(f"{prefix}\tTRUE\t/\tTRUE\t{expire}\t{k}\t{v}\n")
print("".join(netscape_lines))
