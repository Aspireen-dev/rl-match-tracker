# RL Match Tracker

> Un tracker local pour Rocket League : enregistre automatiquement chaque match joué et transforme cette donnée brute en outil d'analyse de progression. Historique détaillé, statistiques agrégées, graphiques de tendance et profil de jeu, sans jamais interagir avec le jeu lui-même.

## Pourquoi ce projet existe

Depuis l'arrivée d'Easy Anti-Cheat, BakkesMod n'est plus utilisable en ligne, et Psyonix n'a publié **aucune application officielle** pour exploiter la Rocket League Stats API (pourtant ouverte aux développeurs). Les joueurs compétitifs sur PC n'ont plus d'outil pour analyser finement leurs performances.

Ce projet comble ce vide avec une application full-stack :

- **Lecture passive** du flux TCP/JSON local émis par le jeu (API officielle, zéro risque anti-cheat)
- **Historisation** de chaque match dans une base locale
- **Analyse** via un dashboard web : win rate, tendances, statistiques par mode, profil de jeu

## Stack technique

| Couche | Techno |
|---|---|
| Back-end | ASP.NET Core (.NET 10), C# |
| Ingestion temps réel | Client TCP asynchrone (flux JSON de la [Rocket League Stats API](https://www.rocketleague.com/developer/stats-api)) |
| Base de données | SQLite (V1) via EF Core, provider-agnostique, migration PostgreSQL planifiée (V2) |
| API | REST (ASP.NET Core Minimal APIs) |
| Front-end | React + TypeScript (Vite), TanStack Query, Recharts |
| Styling | Tailwind CSS |
| Tests (introduits progressivement) | xUnit (back), Vitest + React Testing Library (front) |
| CI (introduite après le socle) | GitHub Actions |

## Documentation (dossier `/docs`)

- [`PRODUCT.md`](docs/PRODUCT.md) : contexte produit, cible, limites, vision (FR)
- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) : architecture technique et décisions (EN)
- [`CONTRIBUTING.md`](docs/CONTRIBUTING.md) : conventions de code et pratiques (EN)
- [`ROADMAP.md`](docs/ROADMAP.md) : backlog itératif V1 → V2 → V3 (FR)
- [`JOURNAL.md`](docs/JOURNAL.md) : journal de progression, session par session (FR)
- [`STACK.md`](docs/STACK.md) : chaque outil du projet expliqué simplement (ce qu'il fait, ce qu'il apporte ici)
- [`PLAYLISTS.md`](docs/PLAYLISTS.md) : table des `PlaylistId` du flux Stats API → mode (captures réelles + source communautaire), stratégie pour les LTM (FR)

## Configuration du jeu

Pour que Rocket League diffuse ses stats, activer la Stats API dans :
`Documents\My Games\Rocket League\TAGame\Config\TAStatsAPI.ini`

```ini
[TAGame.MatchStatsExporter_TA]
PacketSendRate=30
Port=49123
WebPort=49124
```

> ⚠️ D'après la [doc officielle](https://www.rocketleague.com/developer/stats-api), c'est
> `PacketSendRate` qui active l'API (0 = désactivé par défaut), et le fichier ini **n'est
> lu qu'au lancement du jeu** : toute modification impose de **redémarrer Rocket League**.
> Symptôme d'un flux arrêté : le port 49123 est ouvert mais **aucun paquet n'est émis**
> → revérifier le ini (section `[TAGame.MatchStatsExporter_TA]`, `PacketSendRate` entre 1
> et 120) et relancer le jeu.

## Contribuer (setup local)

Après un clone, activer le hook pre-commit (scan de confidentialité des fixtures) :

```bash
git config core.hooksPath .githooks
```

Les captures brutes (`captures/*.jsonl`) contiennent des vrais noms/IDs de joueurs :
elles restent locales (gitignorées) ; seules les fixtures anonymisées
(`tests/anonymize_fixture.py` + `tests/check_fixtures_privacy.py`) sont commitées.
Voir [CONTRIBUTING.md](docs/CONTRIBUTING.md) pour les conventions.

## Statut

Projet d'apprentissage full-stack, en développement itératif. Voir la [roadmap](docs/ROADMAP.md).

## Avertissement

Projet indépendant, non affilié à Psyonix ni Epic Games. L'outil ne fait que consommer le flux local officiel ; il n'injecte rien dans le jeu et n'analyse pas le comportement d'autres joueurs. Les données capturées restent sur la machine du joueur.
