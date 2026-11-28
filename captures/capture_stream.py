#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SONDE DE CAPTURE ONE-OFF — flux Stats API de Rocket League
==========================================================

À QUOI ÇA SERT ?
---------------
Le jeu fait office de SERVEUR TCP sur 127.0.0.1:49123 et broadcast un flux
continu d'objets JSON CONCATÉNÉS SANS SÉPARATEUR (~3 Ko × 30/s) :

    {"Event":"UpdateState","Data":"..."}{"Event":"Goal","Data":"..."}...

Cette sonde s'y connecte EN PARALLÈLE de l'API (le jeu accepte plusieurs
clients) et écrit chaque objet reçu sur SA PROPRE LIGNE dans un fichier
JSONL (JSON Lines = un objet JSON par ligne) :

    captures/stream-20260122-143000.jsonl

Pourquoi un script Python et pas une modif de l'API C# ?
  - Zéro toucher au code projet (src/) : ce fichier vit dans captures/,
    dossier gitignoré prévu pour les outils one-off.
  - json.JSONDecoder().raw_decode fait le découpage "objets collés" en 3 lignes.

LEXIQUE PYTHON RAPIDE (pour grand débutant)
-------------------------------------------
- L'indentation (4 espaces) DÉLIMITE les blocs : pas d'accolades { }.
- def f(): déclare une fonction.  def f() -> int: annonce le type de retour.
- import json   =   using System.Text.Json; en C# (bibliothèque standard,
  installée avec Python, rien à télécharger).
- try/except TypeErreur:   =   try/catch (TypeErreur) en C#.
- with open(...) as f:     =   using var f = new StreamWriter(...) en C#
  (le fichier est fermé automatiquement à la sortie du bloc, même si erreur).
- f"texte {variable}..."   =   $"texte {variable}..." en C# (interpolation).
- x if cond else y         =   cond ? x : y en C# (opérateur ternaire).
- None = null.  len(s) = s.Length.  s[a:b] = s.Substring(a, b - a).
- liste[0] = premier élément (les indices commencent à 0, comme en C#).
- print(..., flush=True) = Console.WriteLine + vidage immédiat du tampon :
  sinon le terminal n'afficherait rien avant plusieurs secondes.

UTILISATION
-----------
    python captures/capture_stream.py [fichier_sortie] [duree_secondes]
    - sans argument : le nom du fichier est auto-généré avec date/heure
    - sans duree    : capture jusqu'à la fin du flux (Ctrl+C pour arrêter)
"""

import codecs   # décodage UTF-8 incrémental (voir bloc 6 plus bas)
import json     # parser/sérialiser du JSON  = System.Text.Json en C#
import socket   # les sockets TCP              = System.Net.Sockets en C#
import sys      # accès aux arguments de la ligne de commande (= string[] args en C#)
import time     # le chronomètre               = System.Diagnostics.Stopwatch en C#
from datetime import datetime  # date/heure pour nommer le fichier de sortie

# Constantes en MAJUScules (convention Python) : hôte et port du serveur = LE JEU.
HOST, PORT = "127.0.0.1", 49123   # 127.0.0.1 = localhost = cette machine


def main() -> int:
    """Point d'entrée du programme. Renvoie 0 si tout s'est bien passé."""

    # ---- 1. Les arguments de la ligne de commande -------------------------
    # sys.argv = liste des arguments tapés après le nom du script.
    # Exemple : "python capture_stream.py out.jsonl 60"
    #           -> sys.argv = ["capture_stream.py", "out.jsonl", "60"]
    # sys.argv[1] = 2e élément (indice 1, car les listes commencent à 0).
    # "X if condition else Y" = ternaire C# "condition ? X : Y" :
    #   si un 1er argument existe, il sert de nom de fichier,
    #   sinon on en génère un avec la date/heure du jour.
    out_path = sys.argv[1] if len(sys.argv) > 1 else f"captures/stream-{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    # Idem pour un éventuel 2e argument : la durée max de capture en secondes.
    # float(...) convertit le texte en nombre décimal (Convert.ToDouble en C#).
    # Si absent -> None (= null en C#) = pas de limite de durée.
    duration_s = float(sys.argv[2]) if len(sys.argv) > 2 else None

    # ---- 2. Connexion au jeu (le serveur TCP) ------------------------------
    # En C# dans le service :  using TcpClient client = new TcpClient();
    #                          await client.ConnectAsync(host, port, ct);
    # create_connection fait les deux en une ligne : crée le client ET connecte.
    # timeout=10 : délai max pour l'établissement de la connexion (10 s).
    sock = socket.create_connection((HOST, PORT), timeout=10)
    # settimeout(1.0) : à partir de maintenant, chaque recv bloquera AU MAXIMUM
    # 1 seconde puis lèvera l'exception socket.timeout si rien n'est arrivé.
    # Ça permet de vérifier régulièrement la durée demandée (équivalent du
    # CancellationToken qu'on teste entre deux tours de boucle côté C#).
    sock.settimeout(1.0)
    print(f"[capture] connecte a {HOST}:{PORT}, ecriture dans {out_path}", flush=True)

    # ---- 3. Préparation des outils de la boucle ---------------------------
    decoder = json.JSONDecoder()  # "usine" qui sait découper du JSON (voir bloc 5)
    # Décodeur UTF-8 INCRÉMENTAL : se souvient des octets d'un caractère
    # incomplet entre deux appels (voir bloc 6). errors="replace" = si un octet
    # est vraiment invalide, on le remplace par � au lieu de planter.
    utf8 = codecs.getincrementaldecoder("utf-8")(errors="replace")
    buf = ""       # tampon TEXTE : ce qui a été reçu mais pas encore découpé en objets
    count = 0      # nombre d'objets JSON écrits dans le fichier
    start = time.monotonic()  # chronomètre interne (en secondes, monotone)

    # ---- 4. La boucle principale -------------------------------------------
    # "with open(...) as out:" ouvre le fichier en écriture ("w" = write,
    # écrase l'ancien contenu) et le FERME AUTOMATIQUEMENT à la fin du bloc,
    # même si une erreur survient (équivalent C# : using var out = ...).
    with open(out_path, "w", encoding="utf-8") as out:

        # while True: = boucle infinie (while (true) en C#) ; on en sort par break.
        while True:

            # -- 4a. Durée max atteinte ? ------------------------------------
            # time.monotonic() - start = nombre de secondes écoulées depuis le début.
            if duration_s is not None and time.monotonic() - start >= duration_s:
                # "is not None" = "!= null" en C#
                print(f"[capture] duree {duration_s}s atteinte, arret.", flush=True)
                break  # sort de la boucle infinie

            # -- 4b. Lire le prochain bloc d'octets reçus ---------------------
            # recv(65536) = lire jusqu'à 65536 octets sur la socket.
            # Équivalent C# : stream.Read(buffer, 0, buffer.Length).
            # On lit des OCTETS BRUTS, jamais "une ligne" : le flux ne contient
            # aucun \n, donc une lecture ligne par ligne bloquerait pour toujours
            # (même piège que ReadLineAsync dans la session 1 du journal).
            try:
                chunk = sock.recv(65536)
            except socket.timeout:
                # Rien reçu pendant 1 s : on retourne au début de la boucle
                # (pour revérifier la durée). "continue" = itération suivante.
                continue
            if not chunk:
                # recv renvoie zéro octet = le serveur (le jeu) a fermé la
                # connexion proprement -> fin de la capture.
                print("[capture] fin de flux (le jeu a ferme la connexion).", flush=True)
                break

            # -- 4c. Octets -> texte (UTF-8) ----------------------------------
            # chunk est un bloc d'octets (bytes). On le convertit en texte.
            # utf8.decode(chunk) renvoie le texte décodé ; si un caractère
            # multi-octets était coupé en deux, ses octets en trop sont gardés
            # DANS le décodeur et ressortiront au prochain appel (bloc 6).
            buf += utf8.decode(chunk)

            # -- 4d. Découper le tampon en objets JSON complets ----------------
            # C'est LE CŒUR du script. raw_decode(buf) = "lis UN objet JSON
            # complet au début de cette chaîne, renvoie-le avec la position où
            # il se termine". Équivalent C# : DeserializeAsyncEnumerable avec
            # topLevelValues: true (qui fait la même chose en streaming).
            while True:
                buf = buf.lstrip()   # sauter espaces/newlines entre deux objets
                if not buf:
                    break            # tampon vide : rien à faire
                try:
                    obj, end = decoder.raw_decode(buf)
                    # obj = l'objet Python (dict) désérialisé
                    # end = index dans buf juste APRÈS la fin de l'objet
                except json.JSONDecodeError:
                    # L'objet en cours est INCOMPLET (on est entre deux recv)
                    # -> on garde buf tel quel et on attend la suite du flux.
                    # (JsonException côté C# = même famille d'erreur.)
                    break
                # -- 4e. Écrire l'objet sur sa propre ligne (JSONL) ------------
                # json.dumps(obj) = re-sérialise l'objet en texte JSON compact.
                # ensure_ascii=False : garder les é/è tels quels (pas \u00e9).
                # + "\n" : retour à la ligne -> un objet par ligne dans le fichier.
                out.write(json.dumps(obj, ensure_ascii=False) + "\n")
                count += 1
                buf = buf[end:]   # slicing : ne garder que ce qui est APRÈS l'objet
                                  # consommé (équivalent C# : buf.Substring(end)).
                if count % 300 == 0:
                    # % = modulo ; toutes les 300 lignes, un log d'avancement.
                    print(f"[capture] {count} messages ecrits...", flush=True)
        # flush() = forcer l'écriture immédiate sur le disque (sinon Python
        # attendrait de remplir un tampon interne avant d'écrire).
        out.flush()

    # ---- 5. Bilan de fin ----------------------------------------------------
    if buf.strip():
        # Il reste du texte non parsé : objet coupé en plein milieu à la fin
        # du flux -> on l'affiche pour le signaler (200 premiers caractères,
        # !r = représentation exacte avec les \n visibles, pour déboguer).
        print(f"[capture] ATTENTION: {len(buf)} octets non parsees en fin de flux: {buf[:200]!r}", flush=True)
    print(f"[capture] termine: {count} messages dans {out_path}", flush=True)
    sock.close()   # fermer proprement la socket
    return 0       # code de retour 0 = succès (équivalent Environment.Exit(0))


# Point d'entrée : ce bloc ne s'exécute que si on lance le fichier directement
# (python capture_stream.py), pas si un autre script l'importe comme module.
# Équivalent C# : la méthode Main().
if __name__ == "__main__":
    sys.exit(main())   # quitter le programme avec le code retour de main()
