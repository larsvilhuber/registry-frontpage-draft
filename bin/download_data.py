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
import urllib.error
import urllib.request

REGISTRY_CSV_URL = "https://www.socialscienceregistry.org/site/csv"


def download(url, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    # Write to a temporary file first so an interrupted download cannot leave a
    # truncated CSV behind for the exporter to consume.
    tmp = path + ".part"
    try:
        with urllib.request.urlopen(url, timeout=300) as response:
            if response.status != 200:
                raise urllib.error.HTTPError(url, response.status, "unexpected status", response.headers, None)
            with open(tmp, "wb") as handle:
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    handle.write(chunk)
    except (urllib.error.URLError, OSError) as err:
        if os.path.exists(tmp):
            os.remove(tmp)
        sys.exit(f"error: download failed: {err}")

    os.replace(tmp, path)
    return os.path.getsize(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=REGISTRY_CSV_URL)
    parser.add_argument("--out", default="exports/trials.csv")
    args = parser.parse_args()

    size = download(args.url, args.out)
    print(f"saved {size / 1e6:.1f} MB to {args.out}")


if __name__ == "__main__":
    main()
