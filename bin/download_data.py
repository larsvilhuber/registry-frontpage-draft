#!/usr/bin/env python3
"""Download the AEA Registry CSV export.

    python3 bin/download_data.py                    # -> exports/trials.csv
    python3 bin/download_data.py --out other.csv

Stdlib only, so the pipeline needs no pip install. Feed the result to
bin/export_hugo_data.py, which turns it into data/trials.json.
"""

import argparse
import os
import sys
import time
import urllib.error
import urllib.request

REGISTRY_CSV_URL = "https://www.socialscienceregistry.org/site/csv"

# urllib's default User-Agent is "Python-urllib/3.x", which web application
# firewalls routinely reject outright -- that is what produced the 403 that
# broke the first deploy.  Identify the client honestly instead of pretending
# to be a browser, so the registry can see who is fetching and contact us.
USER_AGENT = (
    "AEARegistryFrontpageBot/1.0 "
    "(+https://github.com/larsvilhuber/registry-frontpage-draft; static site build)"
)
RETRY_STATUS = {429, 500, 502, 503, 504}


def fetch(url, path, attempts=4):
    """Fetch url to path, retrying on transient failures.

    Writes to a temporary file first so an interrupted download cannot leave a
    truncated CSV behind for the exporter to consume.
    """
    tmp = path + ".part"
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/csv, */*",
    })

    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                with open(tmp, "wb") as handle:
                    while True:
                        chunk = response.read(1 << 20)
                        if not chunk:
                            break
                        handle.write(chunk)
            os.replace(tmp, path)
            return os.path.getsize(path)
        except urllib.error.HTTPError as err:
            cleanup(tmp)
            # A 403 will not fix itself on a retry: it means the registry is
            # refusing this client, not that the server is briefly unwell.
            if err.code not in RETRY_STATUS:
                explain(err)
            last = err
        except (urllib.error.URLError, OSError) as err:
            cleanup(tmp)
            last = err

        if attempt < attempts:
            delay = 2 ** attempt
            print(f"attempt {attempt} failed ({last}); retrying in {delay}s", file=sys.stderr)
            time.sleep(delay)

    sys.exit(f"error: download failed after {attempts} attempts: {last}")


def cleanup(tmp):
    if os.path.exists(tmp):
        os.remove(tmp)


def explain(err):
    """Fail with guidance rather than a bare status code."""
    message = [f"error: the registry refused the request (HTTP {err.code} {err.reason})."]
    if err.code in (401, 403):
        message += [
            "",
            "This is a refusal, not an outage. Likely causes:",
            "  - the User-Agent is being filtered (see USER_AGENT in this file);",
            "  - the source IP is blocked, which commonly affects cloud CI ranges",
            "    such as GitHub Actions runners, in which case no client-side",
            "    change will help and the export needs another route:",
            "    fetch it elsewhere and commit it, mirror it, or ask the registry",
            "    to allow the build.",
        ]
    sys.exit("\n".join(message))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=REGISTRY_CSV_URL)
    parser.add_argument("--out", default="exports/trials.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    size = fetch(args.url, args.out)
    print(f"saved {size / 1e6:.1f} MB to {args.out}")


if __name__ == "__main__":
    main()
