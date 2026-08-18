"""
Minimal Lambda handler used only to verify source-IP diversity across concurrent
invocations -- no k6, no layer, no bundled script, doesn't touch the actual load-test
target. Just calls a public IP-echo service and returns what it saw. See
verify_ip_diversity.py, which deploys and invokes this.
"""

import time
import urllib.request

# AWS-operated, plain-text IP-echo endpoint (no JSON parsing needed) -- commonly used for
# exactly this kind of "what outbound IP am I using" check, e.g. verifying NAT Gateway EIPs.
IP_ECHO_URL = "https://checkip.amazonaws.com"


def handler(event: dict, context) -> dict:
    with urllib.request.urlopen(IP_ECHO_URL, timeout=5) as response:
        ip = response.read().decode().strip()

    # Optional: hold this execution environment busy after fetching the IP, to simulate a
    # longer-running invocation like the real k6 script (~105s ramp/hold/ramp-down) instead
    # of a near-instant call. Confirmed live: a near-instant probe lets Lambda reuse
    # already-warm environments within the same burst faster than genuinely new ones get
    # created, which understates the diversity a longer-running invocation would actually
    # see -- see verify_ip_diversity.py's --hold-seconds.
    hold_seconds = float(event.get("hold_seconds", 0))
    if hold_seconds > 0:
        time.sleep(hold_seconds)

    return {"ip": ip}
