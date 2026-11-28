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
  - un PrimaryId dont l'uid n'est PAS factice (Steam factice = base 76561190000000000
    + petit compteur ; Epic factice = hex 32 chars avec >= 24 zéros de tête) ;
  - toute chaîne de 32 caractères hex (MatchGuid ou autre) avec < 24 zéros de tête
    (les GUID factices sont un compteur complété de zéros).
"""

import json
import re
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "Api.Tests" / "Fixtures"

GENERIC_TEAM_NAMES = {"Blue", "Orange"}
PLACEHOLDER_NAME = re.compile(r"^Player_\d+$")
FAKE_FALLBACK = re.compile(r"^Fake_\d+$")

# Formats "réels" suspects, quel que soit le nom du champ.
PRIMARY_ID_PATTERN = re.compile(r"^[A-Za-z]+\|[0-9a-fA-F]{16,}\|\d+$|^[A-Za-z]+\|\d{15,}\|\d+$")
GUID_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")

# Reconnaissance des valeurs factices produites par anonymize_fixture.py.
FAKE_STEAM_PREFIX = "76561190000000"   # 76561190000000000 + compteur
FAKE_HEX_LEADING_ZEROS = 24            # guid/uid factice = compteur complété de zéros


def is_fake_primary_id(pid):
    parts = pid.split("|")
    if len(parts) != 3:
        return bool(FAKE_FALLBACK.match(pid))
    uid = parts[1]
    # Un uid Epic factice fait 32 chars (hex, parfois que des chiffres) ; un uid
    # Steam (réel ou factice) fait ~17 chiffres. Tester la longueur d'abord, sinon
    # un uid Epic factice composé uniquement de chiffres serait pris pour du Steam.
    if len(uid) == 32:
        return len(uid) - len(uid.lstrip("0")) >= FAKE_HEX_LEADING_ZEROS
    if uid.isdigit():
        return uid.startswith(FAKE_STEAM_PREFIX)
    return False


def is_fake_guid(value):
    return len(value) - len(value.lstrip("0")) >= FAKE_HEX_LEADING_ZEROS


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
                if PRIMARY_ID_PATTERN.match(value) and not is_fake_primary_id(value):
                    problems.append(f"{where}: vrai PrimaryId {value!r}")
            else:
                check_node(value, f"{where}.{key}", problems)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            check_node(item, f"{where}[{i}]", problems)
    elif isinstance(node, str):
        if PRIMARY_ID_PATTERN.match(node) and not is_fake_primary_id(node):
            problems.append(f"{where}: PrimaryId-like non factice {node!r}")
        elif GUID_PATTERN.match(node) and not is_fake_guid(node):
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
