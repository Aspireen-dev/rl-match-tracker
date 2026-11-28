#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extrait le couple (PlaylistId, Arena) + MatchGuid + score final d'une capture JSONL.
Usage : python captures/extract_playlist.py <fichier.jsonl>
"""
import json
import sys
from collections import Counter

def main() -> int:
    path = sys.argv[1]
    playlists, arenas = Counter(), Counter()
    guids = set()
    last_game = None
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            env = json.loads(line)
            n += 1
            if env.get("Event") == "UpdateState":
                d = json.loads(env["Data"])
                g = d["Game"]
                playlists[g.get("PlaylistId")] += 1
                arenas[g.get("Arena")] += 1
                if d.get("MatchGuid"):
                    guids.add(d["MatchGuid"])
                last_game = g
    print(f"{path}: {n} messages")
    print(f"  PlaylistId: {dict(playlists)}   Arena: {dict(arenas)}")
    print(f"  MatchGuid: {sorted(guids)}")
    if last_game:
        print(f"  score final: {[(t['Name'], t['Score']) for t in last_game['Teams']]}  winner={last_game.get('Winner')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
