#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FAUX JEU — rejoue une capture JSONL sur un serveur TCP local (49123 par défaut).

Utile quand Rocket League est éteint : l'API s'y connecte comme au vrai jeu et on
valide le parser C# de façon REPRODUCTIBLE sur les fixtures de captures/.

Le vrai flux = objets JSON concaténés SANS séparateur : on recolle les lignes du
JSONL sans "\n" pour reproduire fidèlement le format brut.

Usage : python captures/replay_capture.py <fichier.jsonl> [--port 49123] [--loop]
  --loop : après l'envoi, garde la connexion ouverte et attend d'autres clients
           (sinon le serveur s'arrête après la première connexion servie).
"""
import socket
import sys

HOST = "127.0.0.1"

def main() -> int:
    path = sys.argv[1]
    port = 49123
    loop = "--loop" in sys.argv
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])

    # Lire le JSONL et recoller les objets SANS séparateur (format brut du jeu)
    with open(path, encoding="utf-8") as f:
        payload = "".join(line.strip() for line in f if line.strip())
    print(f"[replay] {len(payload):,} octets chargés depuis {path}", flush=True)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, port))
    srv.listen(5)
    print(f"[replay] serveur en écoute sur {HOST}:{port} — lance l'API maintenant", flush=True)

    served = 0
    while True:
        conn, addr = srv.accept()
        served += 1
        print(f"[replay] client #{served} connecté depuis {addr}, envoi de la capture...", flush=True)
        try:
            conn.sendall(payload.encode("utf-8"))
            print(f"[replay] capture envoyée ({len(payload):,} octets) au client #{served}", flush=True)
        except OSError as e:
            print(f"[replay] erreur envoi client #{served}: {e}", flush=True)
        finally:
            conn.close()
        if not loop:
            break

    srv.close()
    print(f"[replay] terminé après {served} client(s).", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
