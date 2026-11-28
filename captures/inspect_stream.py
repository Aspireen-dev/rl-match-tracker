#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INSPECTION ONE-OFF d'une capture JSONL du flux Stats API
=========================================================

À QUOI ÇA SERT ?
---------------
Après une capture (capture_stream.py), on a un gros fichier de dizaines de
milliers de lignes. Ce script en fait L'INVENTAIRE automatiquement :

  1. le nombre total de messages (et combien de lignes illisibles) ;
  2. la répartition par type d'Event  (UpdateState × 52000, Goal × 3, ...)
     -> c'est comme ça qu'on découvre quels messages le jeu envoie vraiment ;
  3. pour chaque Event, un exemple de "Data" DÉBALLÉ avec ses clés
     -> voir la structure des données sans ouvrir le gros fichier ;
  4. les MatchGuid distincts trouvés
     -> un MatchGuid = preuve qu'un VRAI MATCH online a été capturé.

POINT PÉDAGOGIQUE : ici on lit le fichier LIGNE PAR LIGNE (for line in f),
parce que NOUS avons écrit le fichier en JSONL (un objet + \n par ligne).
Le flux réseau brut, lui, n'avait AUCUN séparateur -> d'où le raw_decode
côté capture. Deux mondes, deux règles.

LEXIQUE PYTHON UTILISÉ ICI (compléments)
-----------------------------------------
- from collections import Counter : Counter = dictionnaire qui compte tout seul.
  Équivalent C#/LINQ : groupes.GroupBy(e => e.Event).OrderByDescending(g => g.Count())
- dict : {"cle": valeur}  ;  d["cle"] ou d.get("cle", valeur_par_défaut)
  (get = TryGetValue en C# : ne plante pas si la clé manque).
- set : collection sans doublon (comme HashSet en C#).
- fichier ouvert en "r" (read) : for line in f parcourt ligne par ligne.

UTILISATION
-----------
    python captures/inspect_stream.py <fichier.jsonl> [--sample N]
    --sample N = afficher N exemples de Data par Event (1 par défaut)
"""

import json     # parser JSON = System.Text.Json en C#
import sys      # arguments de la ligne de commande (= string[] args en C#)
from collections import Counter  # compteur automatique (voir lexique)


def main() -> int:
    """Lit la capture passée en argument et affiche son inventaire. Renvoie 0."""

    # ---- 1. Arguments -------------------------------------------------------
    # sys.argv = liste des arguments tapés après le nom du script.
    #   "python captures/inspect_stream.py mon.jsonl --sample 3"
    #     -> sys.argv = ["captures/inspect_stream.py", "mon.jsonl", "--sample", "3"]
    # sys.argv[1] n'existe que si un argument a été passé : sinon, afficher
    # l'aide plutôt que de planter avec un traceback illisible (IndexError).
    if len(sys.argv) < 2:
        print("usage: python captures/inspect_stream.py <fichier.jsonl> [--sample N]", flush=True)
        print("exemple: python captures/inspect_stream.py captures/stream-20260122-143000.jsonl", flush=True)
        return 2   # code de retour 2 = erreur d'utilisation (convention Unix : 0 = OK)
    path = sys.argv[1]
    # "--sample" dans sys.argv = test d'appartenance dans une liste ("x in liste"
    # = liste.Contains(x) en C#). On vérifie qu'une valeur suit bien le --sample.
    sample = 1   # valeur par défaut : 1 exemple de Data affiché par Event
    if "--sample" in sys.argv:
        i = sys.argv.index("--sample")          # position de "--sample" dans la liste
        if i + 1 < len(sys.argv):
            sample = int(sys.argv[i + 1])       # int(...) = Convert.ToInt32 en C#
        else:
            print("erreur: --sample attend un nombre après lui (ex: --sample 3)", flush=True)
            return 2

    # ---- 2. Les "accumulateurs" de statistiques ------------------------------
    events = Counter()     # Counter : events["UpdateState"] += 1 compte tout seul
    match_guids = set()    # ensemble de MatchGuid distincts (pas de doublons)
    examples = {}          # dict : Event -> liste de 1..N exemples de Data déballé
    total = 0              # nombre total de lignes lues
    bad = 0                # lignes illisibles (JSON cassé)

    # ---- 3. Lecture ligne par ligne du fichier JSONL -------------------------
    # with open(...) as f : ouverture + fermeture automatique (using en C#).
    # for line in f : itère sur chaque ligne du fichier (le \n est le séparateur,
    # posé par nous lors de la capture).
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()      # strip() = Trim() en C# (enlève espaces et \n)
            if not line:
                continue             # sauter les lignes vides
            total += 1

            # -- 3a. Désérialiser l'enveloppe {"Event": ..., "Data": "..."} -----
            try:
                envelope = json.loads(line)   # = JsonSerializer.Deserialize en C#
            except json.JSONDecodeError:
                bad += 1                      # ligne illisible : on la compte
                continue

            # .get("Event", ...) = TryGetProperty en C# : valeur par défaut si absent.
            event = envelope.get("Event", "<sans Event>")
            events[event] += 1                # le Counter incrémente tout seul

            # -- 3b. DOUBLE DÉSÉRIALISATION ------------------------------------
            # Data est une STRING qui contient du JSON échappé :
            #   "Data": "{\"MatchGuid\":\"...\", ...}"
            # -> il faut reparser cette string pour voir le vrai contenu.
            # (C'est la "double désérialisation" notée dans le journal, que le
            # futur code C# fera aussi : parse enveloppe, puis parse Data.)
            data_raw = envelope.get("Data", "")

            # Garder jusqu'à `sample` exemples par Event (pour voir la structure).
            if len(examples.get(event, [])) < sample:
                try:
                    data = json.loads(data_raw)   # 2e parsing de Data
                except json.JSONDecodeError:
                    data = f"<Data non-JSON: {data_raw[:80]!r}>"
                examples.setdefault(event, []).append(data)
                # setdefault(event, []) = "crée la liste si la clé n'existe pas"

            # -- 3c. Détecter les MatchGuid (signe d'un vrai match online) -------
            # Test rapide AVANT de parser : chercher la sous-chaîne dans le brut.
            # "x in s" = s.Contains(x) en C#.
            if isinstance(data_raw, str) and '"MatchGuid"' in data_raw:
                try:
                    g = json.loads(data_raw).get("MatchGuid")
                    if g:                       # if g: = "si g n'est pas vide/null"
                        match_guids.add(g)      # set : pas de doublon
                except json.JSONDecodeError:
                    pass                        # Data illisible : on ignore

    # ---- 4. Affichage du rapport ---------------------------------------------
    print(f"=== {path} ===")
    print(f"messages: {total} (lignes non parsees: {bad})")

    print(f"\n-- Repartition par Event --")
    # most_common() = tri décroissant du Counter (OrderByDescending en LINQ).
    for event, n in events.most_common():
        print(f"  {n:6d}  {event}")   # {n:6d} = nombre aligné sur 6 caractères

    print(f"\n-- MatchGuid distincts: {len(match_guids)} --")
    for g in sorted(match_guids)[:10]:   # [:10] = les 10 premiers (slicing)
        print(f"  {g}")

    print(f"\n-- Exemples de Data deballe par Event (cles top-level) --")
    for event, datas in examples.items():   # .items() = parcours cle -> valeur
        for i, data in enumerate(datas):     # enumerate = index + valeur (foreach avec compteur)
            if isinstance(data, dict):       # isinstance = "est un dict ?" (test de type)
                # list(data.keys())[:25] = les 25 premières clés du dict.
                # ", ".join(...) = string.Join(", ", ...) en C#.
                keys = ", ".join(list(data.keys())[:25])
                print(f"  [{event} #{i}] dict, cles: {keys}")
            else:
                # type(data).__name__ = nom du type (ex: "str", "list", "int")
                print(f"  [{event} #{i}] {type(data).__name__}: {str(data)[:120]}")
    return 0


# Point d'entrée (équivalent du Main() en C#) : ne s'exécute que si on lance
# le fichier directement.
if __name__ == "__main__":
    sys.exit(main())
