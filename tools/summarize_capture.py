#!/usr/bin/env python3
"""Summarize captures without pretending gestures identify themselves."""
import argparse
from collections import defaultdict
import json


def summarize(path):
    groups = defaultdict(list)
    with open(path) as stream:
        for line in stream:
            row = json.loads(line)
            key = (row["source"], row["type"], row.get("channel"), row.get("identifier"))
            groups[key].append(row.get("value"))
    for (port, kind, channel, identifier), values in sorted(groups.items()):
        if kind in ("note_off", "poly_pressure"):
            continue
        numbers = [v for v in values if isinstance(v, int)]
        print(json.dumps({"source": port, "type": kind, "channel": channel,
                          "identifier": identifier, "count": len(values),
                          "min": min(numbers) if numbers else None,
                          "max": max(numbers) if numbers else None,
                          "first_values": values[:12]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture")
    summarize(parser.parse_args().capture)
