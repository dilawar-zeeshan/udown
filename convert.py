import time
raw = """__Secure-1PAPISID	TpbTKO_wkDZQElgS/Ad9B6L6ZQso3yxBOt	.youtube.com	/	2027-04-11T11:46:41.146Z	51		✓				High	
__Secure-1PSID	g.a0007gj_cmJMD7aVmxAoeqYq3RQJL5tSWXnShdGloI0RThPkUwedcgGrT4rHhSdL5Q53_bVVgAACgYKASQSARASFQHGX2MiU34n2vKsFsVC6jv2uscIqxoVAUF8yKpD_aIWEazMg9wyZtYw-waA0076	.youtube.com	/	2027-04-11T11:46:41.146Z	167	✓	✓				High	
__Secure-1PSIDCC	AKEyXzWW9ySUEbxe4O0lb7HmfcQNHxHkrUJZIZhpV2PF4DO-5-IbS9-nuuFT7PW_dRkFYcLPzQ	.youtube.com	/	2027-03-22T13:03:43.890Z	90	✓	✓				High	
__Secure-1PSIDTS	sidts-CjQBBj1CYrX_GkWn82zZcbpJeFCFgOGvRMjHZEd4LoBkdHy-qX9MZrMikwIPss2mRwa-niGCEAA	.youtube.com	/	2027-03-22T12:54:47.141Z	97	✓	✓				High	
__Secure-3PAPISID	TpbTKO_wkDZQElgS/Ad9B6L6ZQso3yxBOt	.youtube.com	/	2027-04-11T11:46:41.146Z	51		✓	None			High	
__Secure-3PSID	g.a0007gj_cmJMD7aVmxAoeqYq3RQJL5tSWXnShdGloI0RThPkUwedjm__KNbX6hLsjKov8YSFsQACgYKAQ0SARASFQHGX2MikRX2G2KiIHam3uVXQfJM7BoVAUF8yKoIiaJhVnPOxenhT70JXf5E0076	.youtube.com	/	2027-04-11T11:46:41.147Z	167	✓	✓	None			High	
__Secure-3PSIDCC	AKEyXzUVfxOuyZvsTnKEVZGAzZZJ-dWphZWFRhZ-QVA-Yo01pqc3yl48FJCgEfo_SLt3lMO-ow	.youtube.com	/	2027-03-22T13:03:43.890Z	90	✓	✓	None			High	
__Secure-3PSIDTS	sidts-CjQBBj1CYrX_GkWn82zZcbpJeFCFgOGvRMjHZEd4LoBkdHy-qX9MZrMikwIPss2mRwa-niGCEAA	.youtube.com	/	2027-03-22T12:54:47.141Z	97	✓	✓	None			High	
__Secure-ROLLOUT_TOKEN	CL6OkMHV-PqoxgEQ-JrftZqskwMY5snJyLKzkwM%3D	.youtube.com	/	2026-09-18T11:24:24.729Z	64	✓	✓	None	https://youtube.com		Medium	
APISID	nZRiX6FwnuMd2lTP/Air9hfTohRvghylWf	.youtube.com	/	2027-04-11T11:46:41.145Z	40						High	
HSID	AhZ-gp-J8pDwXxJ3L	.youtube.com	/	2027-04-11T11:46:41.145Z	21	✓					High	
LOGIN_INFO	AFmmF2swRQIhAJbf8nCSUeMcMTgj8pyyeGPestvMnRGgU_tmqopL-9n_AiB7mF568JJcsibaPI-R1LVSD21jUUs3LDlG0OGbS7IAHQ:QUQ3MjNmd2dlVDA1cHBNWDNPTW9KQURjb1dHVkpfUG8tUThvUFVJSlZnYzhMM2EtVTE4N3puX0JQekM0bnFrOXppb2F5UEVIOTlMeGdSalJmTFZtQ2UyWDFIeGZnQ2JqbnhBNXp0SDQ4NFhJY3Mwd09vQThnQ3NuX2ZrY2tjT2JRV0p5aTM0dUZONUV5QWFKZ1Bra3R2RlZ4YlFxeVR3dDln	.youtube.com	/	2027-04-11T11:56:28.808Z	329	✓	✓	None			Medium	
PREF	tz=Asia.Karachi	.youtube.com	/	2027-04-26T12:48:33.099Z	19		✓				Medium	
SAPISID	TpbTKO_wkDZQElgS/Ad9B6L6ZQso3yxBOt	.youtube.com	/	2027-04-11T11:46:41.146Z	41		✓				High	
SID	g.a0007gj_cmJMD7aVmxAoeqYq3RQJL5tSWXnShdGloI0RThPkUwedzbctdbyHRHTarKOicuPdjQACgYKAdQSARASFQHGX2MiGqZzC3I_FN2AM7wrmTmDqRoVAUF8yKq1Q59wjTTSzN9IHbgMhJ_H0076	.youtube.com	/	2027-04-11T11:46:41.146Z	156						High	
SIDCC	AKEyXzXwcBZaG35qSZp3kegFV13dVX8gHAP2mHGXx8DHnVJYW-IkMZOVaAzM4Ij1wrX5STNKAA	.youtube.com	/	2027-03-22T13:03:43.890Z	79						High	
SSID	AnuIiLs17OSMZ53cv	.youtube.com	/	2027-04-11T11:46:41.145Z	21	✓	✓				High	
VISITOR_INFO1_LIVE	x-ABf2lfkjU	.youtube.com	/	2026-09-18T13:03:43.889Z	29	✓	✓	None	https://youtube.com		Medium"""

expire = int(time.time()) + 31536000

out = ["# Netscape HTTP Cookie File", "# https://curl.haxx.se/rfc/cookie_spec.html", "# This is a generated file! Do not edit.", ""]

for line in raw.split("\n"):
    if not line.strip(): continue
    parts = line.split("\t")
    if len(parts) >= 2:
        name = parts[0]
        val = parts[1]
        domain = ".youtube.com"
        prefix = "#HttpOnly_.youtube.com" if name.startswith("__Secure") else ".youtube.com"
        out.append(f"{prefix}\tTRUE\t/\tTRUE\t{expire}\t{name}\t{val}")

with open("output.txt", "w") as f:
    f.write("\n".join(out) + "\n")
