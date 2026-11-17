# Contexte produit — RL Match Tracker

*Document produit, en français. Il explique POURQUOI le projet existe, pour QUI, et quelles sont ses limites assumées.*

## Le problème

Rocket League est un jeu compétitif où la progression se joue sur des détails (précision des tirs, arrêts, rotations). Or :

1. Le jeu n'affiche presque rien : quelques stats cumulées, un rang par playlist. Impossible de savoir si l'on progresse ni sur quoi travailler.
2. **BakkesMod**, l'outil historique de suivi des joueurs, est désactivé en ligne depuis l'arrivée d'Easy Anti-Cheat (28 avril 2026) ; son auteur a annoncé l'arrêt du développement le même jour.
3. **Psyonix a ouvert une Stats API officielle** (flux TCP/JSON local diffusé par le jeu lui-même) mais n'a publié **aucune application** pour la consommer.
4. Les trackers web existants (Rocket League Tracker) sont génériques, limités, et dépendent de services tiers qui refusent l'accès API aux développeurs externes.

Résultat : le joueur PC compétitif n'a aujourd'hui aucun outil satisfaisant pour analyser ses propres performances.

## La solution

Une application **locale** (back + front sur la machine du joueur) qui :

1. **Capte** en temps réel le flux officiel des matchs en cours ;
2. **Historise** chaque match joué dans une base de données locale ;
3. **Analyse** : historique détaillé, agrégats (win rate, moyennes par mode), graphiques de tendances sur jours/mois/années, et à terme un profil de jeu (points forts / axes de progrès).

## Cible

- **Persona principal** : joueur PC compétitif régulier (plusieurs sessions/semaine), sous Windows, motivé par sa progression. Il lance l'outil (ou l'outil démarre automatiquement) avant de jouer.
- **Persona secondaire** : streamer / créateur de contenu Rocket League, intéressé par l'overlay live (V3).

## Proposition de valeur

> « Chaque match compte : je vois mes chiffres, mes tendances et mes axes de progression, sans quitter mon PC et sans dépendre d'un service tiers. »

## Ce que le produit N'EST PAS (limites assumées)

- **Pas de données rétroactives** : l'historique commence le jour où l'outil est utilisé. Les milliers d'heures passées ne sont pas récupérables.
- **Pas de rang/MMR automatique** : le flux donne les stats de match, pas le classement par playlist. (Piste : saisie manuelle du rang comme incrément ultérieur.)
- **Pas de lookup d'autres joueurs** : on ne saisit pas l'ID d'un tiers pour voir ses *stats globales* (les API de tracker tierces comme tracker.gg sont fermées aux développeurs externes, et le flux local ne couvre que les matchs où le joueur est présent). En revanche, le flux inclut tous les joueurs du lobby : les stats « moi vs ce joueur » sont donc possibles *sur les matchs partagés*, et cette analyse est listée en réserve dans ROADMAP.md.
- **PC/Windows uniquement** : le socket est local, sur la machine du jeu.
- **Pas un outil anti-triche** : lecture passive uniquement, aucune analyse comportementale d'autrui.

## Sécurité et conformité

- Lecture passive d'un flux **officiel**, conçu pour cet usage, compatible Easy Anti-Cheat. Aucune injection, aucun hooking.
- Pas de compte, pas de mot de passe, pas de token. Les données stockées se limitent à des identifiants de plateforme publics, des pseudos et des stats de match, y compris celles des autres joueurs des lobbies — données personnelles minimales, jamais exposées hors de la machine du joueur.
- Tout reste en local : pas de serveur distant, pas d'exposition réseau (interface en localhost).

## Vision par versions

- **V1 — Fondations** : capter les matchs, les stocker, les lister, dashboard simple (win rate, derniers matchs, moyennes clés).
- **V2 — Analyse** : dashboard complet (tendances, filtres par mode/période, sessions de jeu), migration PostgreSQL avec conservation de l'historique, tests, CI.
- **V3 — Temps réel et contenu** : vue live du match en cours, overlay OBS via SignalR, profil de jeu.

Voir `ROADMAP.md` pour le détail incrément par incrément.

## Sources (état de l'art, vérifié en nov. 2026)

- [Rocket League Stats API — documentation officielle](https://www.rocketleague.com/developer/stats-api)
- [Easy Anti-Cheat dans Rocket League et la fin de BakkesMod (avril 2026)](https://www.trophi.ai/post/easy-anti-cheat-is-coming-to-rocket-league-in-april-2026-what-ranked-players-need-to-know/) — fondement de la section « Le problème »
- Projets communautaires comparables : [rl-stats (Tauri/Rust)](https://github.com/LucasSabena/rl-stats), [rlstatsapi (Python)](https://github.com/manucabral/rlstatsapi)
- Fermeture des accès : [tracker.gg refuse l'accès API pour Rocket League](https://feedback.tracker.gg/t/is-there-anyway-to-get-api-access/21648)