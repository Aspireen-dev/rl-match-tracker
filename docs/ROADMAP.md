# Roadmap itérative — RL Match Tracker

*Document produit, en français. Chaque incrément est petit, livrable et formatif. On ne passe au suivant que lorsque le précédent fonctionne. Les itérations ne portent pas d'estimation de durée : le rythme se constate dans JOURNAL.md, session après session.*

## V1 — Fondations : capter, stocker, afficher

### Itération 0 — Squelette du projet
- [x] Créer le monorepo : `src/Api` (ASP.NET Core vide) + `src/Web` (Vite + React + TS strict) + `docs/`
- [x] Premier endpoint `GET /api/health` qui répond `ok` ; page React qui l'appelle et l'affiche
- [x] Chaîne de dev complète maîtrisée : `dotnet run`, `npm run dev`, proxy Vite vers l'API
- *Apprentissage : structure d'un projet ASP.NET Core moderne, Program.cs, DI, npm/Vite*

### Itération 1 — Se connecter au jeu
- [ ] Activer la Stats API dans le jeu (TAStatsAPI.ini)
- [ ] Client TCP asynchrone (BackgroundService) qui se connecte au socket et logue les messages reçus
- [ ] Deserialiser le JSON en DTOs typés (UpdateState + événements) ; tolérance aux champs inconnus
- [ ] Reconnexion automatique avec backoff si le jeu ferme le flux
- [ ] **Capturer des échantillons JSON réels et les stocker comme fixtures** (base des futurs tests)
- [ ] **Vérifier la fiabilité du champ playlist/mode sur les fixtures réels** (jouer une partie de chaque type : ranked 2v2, casual 3v3, un extra mode) — cf. risque documenté dans ARCHITECTURE.md ; le résultat tranche le plan B
- [ ] Écrire le script d'anonymisation des fixtures (noms et UIDs factices, formats préservés) ; captures brutes gitignorées — cf. CONTRIBUTING.md
- *Apprentissage : async/await avancé, sockets, System.Text.Json, BackgroundService*

### Itération 2 — Persister les matchs
- [ ] Modèle de données : `Match`, `Player`, `MatchPlayer` (EF Core)
- [ ] DbContext, migration initiale, base SQLite créée
- [ ] Logique d'agrégation : détecter début/fin de match dans le flux, écrire le match complet avec tous les joueurs
- [ ] Vérifier en base après une vraie session de jeu
- [ ] Stocker le payload JSON brut consolidé par match (buffer du flux jusqu'à la fin de partie) — décision ARCHITECTURE.md : garantie de recalcul et de rétrocompatibilité
- [ ] Settings de l'application : plateforme + ID du joueur, construction du `PrimaryId` configuré (décision ARCHITECTURE.md § 2.1)
- [ ] Service de validation : le `PrimaryId` configuré apparaît-il dans le lobby courant ?
- *Apprentissage : EF Core, migrations, modélisation relationnelle, LINQ*

### Itération 3 — API REST
- [ ] `GET /api/matches` (paginé) + `GET /api/matches/{id}`
- [ ] `GET /api/stats/overview` (matchs joués, win rate, moyennes buts/arrêts/passes)
- [ ] `GET /api/health` étendu : état de la connexion au jeu
- *Apprentissage : Minimal APIs, DTOs, pagination, validation*

### Itération 4 — Dashboard V1
- [ ] TanStack Query + hook d'API ; page « Matchs » (liste + filtre mode) ; page « Détail d'un match »
- [ ] Page « Dashboard » : cartes clés (win rate, matchs joués, moyennes) + 1-2 graphiques simples (buts/match sur les 30 derniers jours)
- [ ] Indicateur « jeu connecté »
- [ ] Page « Réglages » (plateforme + ID) ; indicateur « joueur identifié / non trouvé »
- *Apprentissage : composants React, hooks, état serveur, Recharts*

**🚀 Jalon V1 : lancer le jeu avec l'outil ouvert, jouer, puis voir le dashboard se remplir.**

## V2 — Analyse

### Itération 5 — Tests sur l'existant
- [ ] Parser (fixtures réels de l'itération 1), calculs d'agrégats (fonctions pures), endpoints (WebApplicationFactory)
- [ ] Composants front clés (Vitest + RTL)
- *Apprentissage : xUnit, testing d'API, tests front. Fondation qui sécurise toutes les itérations suivantes.*

### Itération 6 — CI GitHub Actions
- [ ] Workflow : build + tests + lint à chaque push
- [ ] Repasser `npm audit` et traiter les 5 advisories constatées à l'itération 0 (ReDoS sur la chaîne picomatch → tinyglobby → vite ; ne pas utiliser `--force`, qui rétrograderait Vite)
- *Apprentissage : CI, GitHub Actions. Naturel une fois les tests écrits.*

### Itération 7 — Migration SQLite → PostgreSQL
- [ ] Docker + conteneur PostgreSQL, pgAdmin
- [ ] **Sauvegarde du fichier `.db` AVANT le premier transfert** (le version control protège le code, pas la donnée)
- [ ] Utilitaire de transfert de données ; tests passant sur les deux providers
- *Apprentissage : PostgreSQL, Docker, migrations de données. Se fait après tests + CI : la migration est l'exercice qui a le plus besoin du filet de sécurité.*

### Itération 8 — Sessions de jeu
- [ ] Entité `Session` (groupement de matchs par intervalle de temps), intégration à l'API et au dashboard
- *Apprentissage : modélisation temporelle, requêtes de groupement.*

### Itération 9 — Dashboard avancé
- [ ] Tendances mois/année, filtres par mode/période, stats par adversaire rencontré, alerte « tilt » (série de défaites)
- *Apprentissage : requêtes d'analyse complexes, dataviz avancée.*

**🚀 Jalon V2 : un dashboard d'analyse complet sur un historique fiable et testé, migré sans perte sur PostgreSQL.**

## V3 — Temps réel et contenu

- Vue **live** du match en cours (SignalR du back vers le front)
- **Overlay OBS** (page dédiée consommable en source navigateur)
- Profil de jeu : points forts / axes de progrès déduits des stats
- Emballage : publication self-contained + lancement au démarrage optionnel
- *Apprentissage : WebSockets/SignalR, packaging/distribution*

## Idées en réserve (non engagées)

- Saisie manuelle du rang/MMR à intervalles réguliers → courbe de progression
- Export CSV/JSON de l'historique
- Mode sombre, i18n
- Stats « moi vs joueur X » sur tout l'historique
- Alertes de but dans l'overlay (raffinement V3, non engagé)

## Règles de la roadmap

1. Un incrément à la fois. Pas de V2 avant que la V1 tourne de bout en bout.
2. Une session = un objectif unique.
3. Toute idée nouvelle va dans « Idées en réserve », pas dans l'incrément courant.
4. Quand un incrément est terminé, cocher les items et mettre à jour ce document.
