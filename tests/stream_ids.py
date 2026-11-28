#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Formats des identifiants du flux Stats API de Rocket League, PAR PLATEFORME,
et reconnaissance des valeurs factices produites par anonymize_fixture.py.

Partagé par :
  - tests/anonymize_fixture.py      (produit les valeurs factices)
  - tests/check_fixtures_privacy.py (vérifie qu'aucune valeur réelle ne fuite)

FORMAT GÉNÉRAL
--------------
PrimaryId = "Platform|Uid|Splitscreen" (séparateur "|")
    ex. "Steam|76561198149344717|0"
Splitscreen = index du joueur local sur la machine (0, 1, ...).

MatchGuid = GUID de 32 caractères hexadécimaux SANS tirets, en majuscules :
    ex. "FAD7CC7A11F1E756688E47A4EA6BEC4F"

PLATEFORMES CONNUES (observées dans captures/)
-----------------------------------------------
Chaque plateforme a son PROPRE alphabet d'uid — d'où une spec par plateforme :
  Steam     SteamID64 : 17 chiffres commençant par 7656119
            (base 76561197960265728)  ex. 76561198149344717
  Epic      Epic Account ID : 32 caractères hexadécimaux
            ex. 02301f8c7555421d9af6002a718b84d6
  PS4       18-19 chiffres (observé : 19)  ex. 7799777708282878931
  XboxOne   XUID : 16 chiffres             ex. 2535425560532703
  Unknown   pas de login (menu) : uid "0"
Une plateforme inconnue (ex. Switch demain) retombe sur la règle générique :
uid hex >= 16 chars OU numérique >= 15 chiffres.

VALEURS FACTICES (produites par anonymize_fixture.py)
-----------------------------------------------------
Chaque plateforme a sa fabrique de faux uid, qui GARDE LA FORME du vrai :
  - Steam : 76561190000000000 + compteur -> préfixe "76561190000000" qu'aucun
    vrai SteamID64 ne peut avoir (les valides sont >= 76561197960265728) ;
  - Epic  : compteur écrit en 32 hex -> >= 24 zéros de tête (un vrai uid
    aléatoire a une probabilité ~16^-24 d'en avoir autant : impossible) ;
  - PS4 / XboxOne : compteur complété de zéros à la longueur du vrai uid
    (un vrai uid numérique ne commence jamais par "0").
"""

import re

# ---- Fabriques de faux uid (compteur -> string, même forme que le vrai) ----


def _fake_steam_uid(counter):
    return str(76561190000000000 + counter)


def _fake_hex_uid(counter):
    return f"{counter:032x}"


def _fake_numeric_uid(length):
    def fake(counter):
        return str(counter).zfill(length)
    return fake


# ---- Spécification PAR PLATEFORME : plateforme -> (regex uid réel, fabrique faux uid) ----

PLATFORM_SPECS = {
    "Steam":   (re.compile(r"^7656119\d{10}$"), _fake_steam_uid),   # 17 chiffres, préfixe 7656119
    "Epic":    (re.compile(r"^[0-9a-fA-F]{32}$"), _fake_hex_uid),   # 32 caractères hex
    "PS4":     (re.compile(r"^\d{18,19}$"), _fake_numeric_uid(19)), # observé : 19 chiffres
    "XboxOne": (re.compile(r"^\d{16}$"), _fake_numeric_uid(16)),    # XUID : 16 chiffres
    "Unknown": (re.compile(r"^0$"), lambda counter: "0"),           # menu, pas de login
}

# Règle générique pour une plateforme inconnue (Switch, ...) : uid hex ou numérique long.
_GENERIC_HEX_UID = re.compile(r"^[0-9a-fA-F]{16,}$")
_GENERIC_NUM_UID = re.compile(r"^\d{15,}$")

# MatchGuid = exactement 32 caractères hexadécimaux (majuscules ou minuscules).
GUID_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")

_HEX_DIGITS = set("0123456789abcdefABCDEF")


def parse_primary_id(value):
    """Découpe "Platform|Uid|Splitscreen" -> (platform, uid, splitscreen), ou None si invalide.

    L'uid est validé avec la spec de SA plateforme (format exact), ou la règle
    générique si la plateforme est inconnue.
    """
    if not isinstance(value, str):
        return None
    parts = value.split("|")
    if len(parts) != 3:
        return None
    platform, uid, splitscreen = parts
    # isalnum et pas isalpha : "PS4" contient un chiffre.
    if not platform.isalnum() or not splitscreen.isdigit():
        return None
    spec = PLATFORM_SPECS.get(platform)
    if spec is not None:
        uid_ok = spec[0].match(uid) is not None
    else:
        uid_ok = _GENERIC_HEX_UID.match(uid) is not None or _GENERIC_NUM_UID.match(uid) is not None
    return (platform, uid, splitscreen) if uid_ok else None


def is_primary_id(value):
    """True si value ressemble à un PrimaryId réel "Platform|Uid|Splitscreen"."""
    return parse_primary_id(value) is not None


def is_guid(value):
    """True si value ressemble à un MatchGuid réel (32 caractères hex)."""
    return isinstance(value, str) and GUID_PATTERN.match(value) is not None


def is_hex_uid(uid):
    """True si uid est hexadécimal avec AU MOINS UNE LETTRE a-f (forme Epic).

    Un nombre pur (Steam/PS4/Xbox) n'est fait que de chiffres, qui sont aussi
    des chiffres hexadécimaux valides : d'où le test sur les lettres.
    """
    return (
        isinstance(uid, str)
        and len(uid) >= 16
        and all(c in _HEX_DIGITS for c in uid)
        and any(c in "abcdefABCDEF" for c in uid)
    )


def fake_uid_for(platform, counter, real_uid):
    """Faux uid pour une plateforme connue (même forme que le vrai), ou imitation
    de l'alphabet du vrai uid pour une plateforme inconnue."""
    spec = PLATFORM_SPECS.get(platform)
    if spec is not None:
        return spec[1](counter)
    return f"{counter:032x}" if is_hex_uid(real_uid) else str(76561190000000000 + counter)


# ---- Reconnaissance des valeurs factices (contrepartie des fabriques ci-dessus) ----

FAKE_STEAM_PREFIX = "76561190000000"  # 76561190000000000 + compteur
FAKE_HEX_LEADING_ZEROS = 24           # uid/GUID hex factice = compteur complété de zéros


def _leading_zeros(value):
    return len(value) - len(value.lstrip("0"))


def is_fake_hex32(value):
    """True si une string de 32 hex est un compteur factice (>= 24 zéros de tête)."""
    return len(value) == 32 and _leading_zeros(value) >= FAKE_HEX_LEADING_ZEROS


def is_fake_primary_id(pid):
    """True si un PrimaryId est une valeur factice produite par l'anonymiseur.

    Règles, quel que soit la plateforme :
      - uid de 32 chars  -> factice si >= 24 zéros de tête (compteur hex) ;
      - uid numérique    -> factice si commence par "0" (compteur complété de
        zéros) ou par le préfixe Steam factice "76561190000000".
    """
    parsed = parse_primary_id(pid)
    if parsed is None:
        return False
    uid = parsed[1]
    if len(uid) == 32:
        return is_fake_hex32(uid)
    if uid.isdigit():
        return uid.startswith("0") or uid.startswith(FAKE_STEAM_PREFIX)
    return False


def is_fake_guid(value):
    """True si un MatchGuid de 32 hex est un GUID factice (compteur + zéros)."""
    return is_guid(value) and is_fake_hex32(value)
