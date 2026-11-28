#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Formats des identifiants du flux Stats API de Rocket League, et reconnaissance
des valeurs factices produites par anonymize_fixture.py.

Partagé par :
  - tests/anonymize_fixture.py    (produit les valeurs factices)
  - tests/check_fixtures_privacy.py (vérifie qu'aucune valeur réelle ne fuite)

FORMATS RÉELS (observés dans captures/)
----------------------------------------
PrimaryId = "Platform|Uid|Splitscreen", séparés par des "|" :
    Steam|76561198149344717|0                     uid = SteamID64, 17 chiffres
    Epic|02301f8c7555421d9af6002a718b84d6|0       uid = 32 caractères HEXADÉCIMAUX
    PS4|7799777708282878931|0                     uid = 19 chiffres
    XboxOne|2535425560532703|0                    uid = 16 chiffres
    Unknown|0|0                                   uid fictif "0" (menu, pas de login)
  -> l'uid est HEXADÉCIMAL pour Epic, NUMÉRIQUE pour Steam/PS4/XboxOne.
  -> Splitscreen = index du joueur local sur la machine (0, 1, ...).

MatchGuid = GUID de 32 caractères hexadécimaux SANS tirets, en majuscules :
    FAD7CC7A11F1E756688E47A4EA6BEC4F

VALEURS FACTICES (produites par anonymize_fixture.py)
-----------------------------------------------------
  - uid numérique factice : 76561190000000000 + compteur, donc préfixe
    "76561190000000". Aucun vrai SteamID64 ne peut avoir ce préfixe : les
    SteamID64 valides sont >= 76561197960265728 (ils commencent par 7656119
    suivi d'un chiffre >= 7, typiquement "76561198...").
  - uid hex / GUID factice : compteur écrit en 32 hex, donc >= 24 zéros de
    tête. Un vrai identifiant aléatoire a une probabilité ~16^-24 d'avoir
    autant de zéros : impossible en pratique.
"""

import re

# ---- Fragments nommés : chaque morceau du pattern a un nom explicite ----

_PLATFORM = r"[A-Za-z]+"       # nom de plateforme : lettres uniquement
_HEX_UID = r"[0-9a-fA-F]{16,}"  # uid hexadécimal d'au moins 16 chars (Epic = 32)
_NUM_UID = r"\d{15,}"          # uid numérique d'au moins 15 chiffres (Steam 17, PS4 19, XboxOne 16)
_SPLITSCREEN = r"\d+"          # index du joueur local en splitscreen (0, 1, ...)

# PrimaryId complet = "Platform|Uid|Splitscreen", avec uid hex (Epic) OU numérique.
PRIMARY_ID_PATTERN = re.compile(
    rf"^{_PLATFORM}\|{_HEX_UID}\|{_SPLITSCREEN}$"
    r"|"
    rf"^{_PLATFORM}\|{_NUM_UID}\|{_SPLITSCREEN}$"
)

# MatchGuid = exactement 32 caractères hexadécimaux (majuscules ou minuscules).
GUID_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")

_HEX_DIGITS = set("0123456789abcdefABCDEF")


def is_primary_id(value):
    """True si value ressemble à un PrimaryId réel "Platform|Uid|Splitscreen"."""
    return isinstance(value, str) and PRIMARY_ID_PATTERN.match(value) is not None


def is_guid(value):
    """True si value ressemble à un MatchGuid réel (32 caractères hex)."""
    return isinstance(value, str) and GUID_PATTERN.match(value) is not None


def is_hex_uid(uid):
    """True si uid est un identifiant hexadécimal (forme Epic, >= 16 caractères).

    Doit contenir AU MOINS UNE LETTRE a-f : un nombre pur (Steam/PS4/Xbox) n'est
    composé que de chiffres, qui sont aussi des chiffres hexadécimaux valides.
    """
    return (
        isinstance(uid, str)
        and len(uid) >= 16
        and all(c in _HEX_DIGITS for c in uid)
        and any(c in "abcdefABCDEF" for c in uid)
    )


# ---- Reconnaissance des valeurs factices (contrepartie des règles ci-dessus) ----

FAKE_STEAM_PREFIX = "76561190000000"  # 76561190000000000 + compteur
FAKE_HEX_LEADING_ZEROS = 24           # uid/GUID factice = compteur complété de zéros


def _leading_zeros(value):
    return len(value) - len(value.lstrip("0"))


def is_fake_hex32(value):
    """True si une string de 32 hex est un compteur factice (>= 24 zéros de tête)."""
    return len(value) == 32 and _leading_zeros(value) >= FAKE_HEX_LEADING_ZEROS


def is_fake_primary_id(pid):
    """True si un PrimaryId est une valeur factice produite par l'anonymiseur."""
    parts = pid.split("|")
    if len(parts) != 3:
        return False
    uid = parts[1]
    # Tester la longueur 32 d'abord : un uid Epic factice composé uniquement de
    # chiffres ("...0003") ne doit pas être pris pour un uid Steam.
    if len(uid) == 32:
        return is_fake_hex32(uid)
    if uid.isdigit():
        return uid.startswith(FAKE_STEAM_PREFIX)
    return False


def is_fake_guid(value):
    """True si un MatchGuid de 32 hex est un GUID factice (compteur + zéros)."""
    return is_guid(value) and is_fake_hex32(value)
