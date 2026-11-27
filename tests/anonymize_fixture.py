#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anonymise une capture brute du flux Stats API en fixture commitable.

Règle (CONTRIBUTING.md, "Fixture privacy") : les captures brutes (dossier captures/,
gitignoré) contiennent les vrais noms et PrimaryId des joueurs (y compris tiers).
Seules les fixtures produites par CE script sont commitées (tests/Api.Tests/Fixtures/).

Anonymisation, déterministe (même entrée -> même sortie, mappings cohérents dans tout
le fichier : un même joueur garde le même faux nom partout) :
  - noms de joueurs (Name, PlayerName, Scorer/Assister/MainTarget/SecondaryTarget,
    Teams[].Name sauf "Blue"/"Orange" qui sont génériques)
      -> "Player_01", "Player_02", ... dans l'ordre d'apparition
  - PrimaryId "Platform|Uid|Splitscreen" -> "Platform|<uid factice>|<même Splitscreen>"
      (format préservé ; uid factice : numérique type Steam, ou hex 32 chars pour Epic)
  - MatchGuid -> GUID factice (32 hex), cohérent par match
  - tout le reste (scores, stats, Arena, PlaylistId, Loadout cosmétique...) est conservé

Usage :
    python tests/anonymize_fixture.py [--sample N] <capture_brute.jsonl> <fixture_sortie.jsonl>

    --sample N : au lieu du match complet (trop lourd pour git), garde un extrait
                 représentatif : les N premières lignes + les N dernières + TOUS les
                 événements discrets (Event != "UpdateState" : buts, début/fin de match...).
                 N = 100 par défaut. Le brut complet reste dans captures/ (gitignoré).
"""
import json
import sys

# Noms d'équipe génériques du jeu : PAS des données personnelles, on les garde.
GENERIC_TEAM_NAMES = {"Blue", "Orange"}


class Anonymizer:
    def __init__(self):
        self._names = {}   # vrai nom -> "Player_XX"
        self._pids = {}    # vrai PrimaryId -> faux PrimaryId
        self._guids = {}   # vrai MatchGuid -> faux GUID
        self._counter = 0

    def _next(self, prefix):
        self._counter += 1
        return f"{prefix}_{self._counter:02d}"

    def fake_name(self, name):
        if name not in self._names:
            self._names[name] = self._next("Player")
        return self._names[name]

    def fake_primary_id(self, pid):
        # Format à préserver : "Platform|Uid|Splitscreen"
        if pid not in self._pids:
            parts = pid.split("|")
            if len(parts) != 3:
                self._pids[pid] = self._next("Fake")  # format inattendu : on dégage
            else:
                platform, _, splitscreen = parts
                if platform == "Epic":
                    fake_uid = f"{self._counter:032x}"          # Epic = hex 32 chars
                else:
                    fake_uid = str(76561190000000000 + self._counter)  # Steam-like = numérique
                self._pids[pid] = f"{platform}|{fake_uid}|{splitscreen}"
        return self._pids[pid]

    def fake_guid(self, guid):
        if guid not in self._guids:
            self._guids[guid] = f"{self._counter + 1:032X}"  # GUID factice, 32 hex
        return self._guids[guid]

    def anonymize(self, node):
        """Parcourt récursivement dict/list et anonymise les champs personnels connus."""
        if isinstance(node, dict):
            # Un objet "Team" se reconnaît à ses couleurs (ColorPrimary/ColorSecondary).
            # Seul Game.Teams[].Name peut garder les noms génériques Blue/Orange ;
            # un joueur peut s'appeler "Blue" -> dans Players[] (pas de ColorPrimary),
            # son Name est toujours anonymisé.
            is_team = "ColorPrimary" in node
            out = {}
            for key, value in node.items():
                if key == "MatchGuid" and isinstance(value, str):
                    out[key] = self.fake_guid(value)
                elif key == "PrimaryId" and isinstance(value, str):
                    out[key] = self.fake_primary_id(value)
                elif key in ("Name", "PlayerName") and isinstance(value, str):
                    out[key] = value if (is_team and value in GENERIC_TEAM_NAMES) else self.fake_name(value)
                else:
                    out[key] = self.anonymize(value)
            return out
        if isinstance(node, list):
            return [self.anonymize(item) for item in node]
        return node


def main() -> int:
    # Parse les arguments : --sample N (optionnel) puis <src> <dst>
    args = sys.argv[1:]
    sample = None
    if "--sample" in args:
        i = args.index("--sample")
        sample = int(args[i + 1]) if i + 1 < len(args) else 100
        del args[i:i + 2]
    if len(args) < 2:
        print("usage: python tests/anonymize_fixture.py [--sample N] <capture_brute.jsonl> <fixture_sortie.jsonl>", flush=True)
        return 2
    src, dst = args

    # Lecture de toute la capture en mémoire (JSONL = une enveloppe par ligne)
    with open(src, encoding="utf-8") as fin:
        envelopes = [json.loads(line) for line in fin if line.strip()]

    # --sample : sélection d'un extrait représentatif (ordre d'origine conservé,
    # pour que les compteurs de l'anonymiseur restent déterministes)
    if sample is not None:
        n = len(envelopes)
        keep = set(range(min(sample, n))) | set(range(max(0, n - sample), n))
        for i, env in enumerate(envelopes):
            if env.get("Event") != "UpdateState":   # événements discrets = toujours gardés
                keep.add(i)
        envelopes = [envelopes[i] for i in sorted(keep)]
        print(f"[anonymize] échantillon: {len(envelopes)} lignes gardées sur {n}", flush=True)

    anonymizer = Anonymizer()
    count = 0
    with open(dst, "w", encoding="utf-8") as fout:
        for envelope in envelopes:
            if "Data" in envelope and isinstance(envelope["Data"], str):
                # Data = JSON échappé dans une string : on anonymise le contenu re-parsé
                envelope["Data"] = json.dumps(anonymizer.anonymize(json.loads(envelope["Data"])), ensure_ascii=False)
            else:
                envelope = anonymizer.anonymize(envelope)
            fout.write(json.dumps(envelope, ensure_ascii=False) + "\n")
            count += 1

    print(f"[anonymize] {count} messages -> {dst}")
    print(f"[anonymize] {len(anonymizer._names)} noms, {len(anonymizer._pids)} PrimaryId, {len(anonymizer._guids)} MatchGuid remplacés", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
