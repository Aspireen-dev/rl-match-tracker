# Table des `PlaylistId` (flux Stats API)

> **LTM** = *Limited Time Mode* : mode événementiel temporaire (Heatseeker, Spike Rush,
> Rocket Labs, Arcade…) qui tourne par roulement, côté casual. Ses `PlaylistId` sont
> hauts et rotatifs → voir « Modes temporaires » en bas.

`Game.PlaylistId` dans les événements `UpdateState`. Psyonix ne publie aucune table
officielle : cette table est maintenue au fil des matchs joués.

## Correspondance PlaylistId → mode

| PlaylistId | Mode |
|---|---|
| 1 | Casual 1v1 |
| 2 | Casual 2v2 |
| 3 | Casual 3v3 |
| 4 | Casual 4v4 (Chaos) |
| 10 | Ranked 1v1 (Duel) |
| 11 | Ranked 2v2 (Doubles) |
| 13 | Ranked 3v3 (Standard) |
| 27 | Hoops |
| 28 | Rumble |
| 29 | Dropshot |
| 30 | Snow Day |
| 34 | Tournois |
| 61 | 4v4 (Chaos) |
| 63 | Heatseeker |

Arènes vues : casual 2v2 → `NeoTokyo_Arcade_P`, ranked 2v2 → `CHN_Stadium_P`,
ranked 3v3 → `cs_day_p`, Hoops → `HoopsStadium_P`, Rumble → `Labs_DoubleGoal_V2_P`.

## Modes temporaires (LTM)

IDs **rotatifs** (souvent élevés), impossibles à lister statiquement. Stratégie :
stocker le `PlaylistId` brut ; si inconnu de cette table → fallback sur `Game.Arena`
(souvent explicite, ex. `HoopsStadium_P`) ou afficher « Playlist #ID » ; compléter
cette table au fil des matchs joués.

## Utilisation dans le projet

- On stocke **toujours le `PlaylistId` brut** dans `Match` (itération 2) : aucune perte.
- Le mapping nom ↔ ID servira à l'affichage (itération 3+) : un fichier C# dédié
  (`PlaylistCatalog`) sera créé à ce moment-là à partir de cette table (YAGNI).
- `Game.Arena` complète le mode pour les extra modes (arènes dédiées).
