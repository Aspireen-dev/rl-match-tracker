#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GARDE-FOU CONFIDENTIALITÉ — vérifie qu'aucune fixture commitée ne contient de
donnée personnelle réelle (noms de joueurs tiers, vrais IDs de plateforme,
vrais MatchGuid).

Complément de tests/anonymize_fixture.py : l'anonymiseur produit la fixture,
ce script PROUVE qu'elle est propre. Lancé par le hook pre-commit
(.githooks/pre-commit) et utilisable à la main :

    python tests/check_fixtures_privacy.py [fichier.jsonl ...]

Sans argument : scanne tous les tests/Api.Tests/Fixtures/*.jsonl.
Code de sortie : 0 = propre, 1 = fuite détectée (détail imprimé), 2 = erreur usage.

Ce qui est considéré comme une fuite :
  - un Name/PlayerName qui n'est ni un placeholder "Player_NN" ni le nom
    d'équipe générique Blue/Orange (dans un objet Team, reconnaissable à ColorPrimary) ;
  - un PrimaryId dont l'uid n'est PAS factice (les factices sont reconnaissables :
    Steam = préfixe 76561190000000, Epic = hex 32 avec >= 24 zéros de tête,
    PS4/XboxOne = numérique commençant par "0" — voir tests/stream_ids.py) ;
  - toute chaîne de 32 caractères hex (MatchGuid ou autre) avec < 24 zéros de tête
    (les GUID factices sont un compteur complété de zéros).
"""

import json
import re
import sys
from pathlib import Path

# Formats d'identifiants du flux + reconnaissance des valeurs factices,
# partagés avec anonymize_fixture.py — voir tests/stream_ids.py pour le détail.
from stream_ids import is_fake_guid, is_fake_primary_id, is_guid, is_primary_id

FIXTURES_DIR = Path(__file__).resolve().parent / "Api.Tests" / "Fixtures"

GENERIC_TEAM_NAMES = {"Blue", "Orange"}
PLACEHOLDER_NAME = re.compile(r"^Player_\d+$")


def check_node(node, where, problems):
    """Parcourt récursivement dict/list/str et enregistre les fuites trouvées."""
    if isinstance(node, dict):
        is_team = "ColorPrimary" in node
        for key, value in node.items():
            lower = key.lower()
            if lower in ("name", "playername") and isinstance(value, str):
                if not PLACEHOLDER_NAME.match(value) and not (is_team and value in GENERIC_TEAM_NAMES):
                    problems.append(f"{where}: nom non anonymisé {key}={value!r}")
            elif lower == "primaryid" and isinstance(value, str):
                if is_primary_id(value) and not is_fake_primary_id(value):
                    problems.append(f"{where}: vrai PrimaryId {value!r}")
            else:
                check_node(value, f"{where}.{key}", problems)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            check_node(item, f"{where}[{i}]", problems)
    elif isinstance(node, str):
        if is_primary_id(node) and not is_fake_primary_id(node):
            problems.append(f"{where}: PrimaryId-like non factice {node!r}")
        elif is_guid(node) and not is_fake_guid(node):
            problems.append(f"{where}: GUID/uid 32 hex non factice {node!r}")


def check_file(path):
    problems = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip():
                continue
            where = f"{path}:{lineno}"
            try:
                envelope = json.loads(line)
            except json.JSONDecodeError as e:
                problems.append(f"{where}: ligne non JSON ({e})")
                continue
            if isinstance(envelope, dict) and isinstance(envelope.get("Data"), str):
                try:
                    envelope["Data"] = json.loads(envelope["Data"])
                except json.JSONDecodeError:
                    pass  # Data illisible : check_node traitera la string telle quelle
            check_node(envelope, where, problems)
    return problems


def main() -> int:
    args = sys.argv[1:]
    files = [Path(a) for a in args] if args else sorted(FIXTURES_DIR.glob("*.jsonl"))
    if not files:
        print("[privacy] aucun fichier à scanner", flush=True)
        return 2

    all_problems = []
    for path in files:
        all_problems.extend(check_file(path))

    if all_problems:
        print(f"[privacy] FUITE DÉTECTÉE ({len(all_problems)} occurrence(s)) :", flush=True)
        for p in all_problems[:50]:
            print(f"  - {p}", flush=True)
        if len(all_problems) > 50:
            print(f"  ... et {len(all_problems) - 50} de plus", flush=True)
        print("[privacy] Refus du commit : anonymise d'abord avec tests/anonymize_fixture.py", flush=True)
        return 1

    print(f"[privacy] OK : {len(files)} fichier(s) scanné(s), aucune donnée personnelle réelle", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
