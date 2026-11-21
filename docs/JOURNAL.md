# Journal de progression

*Une entrée par session de travail. Le "quoi" est coché dans ROADMAP.md,
le "comment" est documenté par le code : ce journal garde le pourquoi de
la progression — notions acquises, pièges résolus, décisions tranchées.*

## 2026-11-21 — Itération 1, session 1 : client TCP du flux Stats API

- **Objectif** : BackgroundService connecté au socket du jeu (localhost:49123),
  logs des messages reçus, reconnexion automatique avec backoff.
- **Fait** : `GameStatsOptions` (IOptions bindé depuis appsettings),
  `GameStatsIngestionService` (BackgroundService + TcpClient + parsing
  streaming), enregistré dans `Program.cs` (`AddHostedService` +
  `Configure<>`). Vérifié en match réel : connexion stable, messages reçus
  et logués (~30/s), backoff 2s→30s quand le jeu est éteint.
- **Appris** : le jeu est le SERVEUR TCP, nous le client ; DI d'ASP.NET Core
  (injection par constructeur, `ILogger<T>` catégorisé, `IOptions<T>.Value`) ;
  le logger console vient du bootstrap et se filtre via `Logging:LogLevel` ;
  `using var`, catch filtrés (`when`), backoff exponentiel.
- **Découverte clé (format du flux)** : objets
  `{"Event":"...","Data":"<json échappé>"}` concaténés SANS séparateur
  (~3 Ko × 30/s). `ReadLineAsync` bloquait (pas de newline) ;
  `DeserializeAsyncEnumerable` en mode array par défaut plantait →
  bonne API : `DeserializeAsyncEnumerable<T>(stream, topLevelValues: true)`
  (.NET 9+). `Data` = JSON sérialisé dans une string → double
  désérialisation à prévoir pour les DTOs.
- **Pièges résolus** : cause racine du « rien ne logue » = le flux est une
  succession d'objets JSON concaténés SANS séparateur (sonde TCP PowerShell :
  0 newline sur des dizaines de Ko) → `ReadLineAsync` bloquait, puis
  `DeserializeAsyncEnumerable` en mode array par défaut levait une
  JsonException (il attend `[`, pas `{`) → spam de reconnexions.
  Fix : `topLevelValues: true` (.NET 9+). Note rétrospective : le process
  fantôme lancé par l'IDE n'était pas la cause (le jeu broadcast à plusieurs
  clients) — il dispersait juste les logs ; d'où la règle : lancer l'API
  depuis un terminal externe, une seule instance.
- **Décisions** : parsing via `topLevelValues: true` (ARCHITECTURE.md) ;
  types explicites plutôt que `var` (CONTRIBUTING.md).
- **Prochaines étapes** : DTOs typés (UpdateState + événements,
  tolérance aux champs inconnus) ; capturer des fixtures réelles ; vérifier
  la fiabilité du champ playlist/mode (risque ARCHITECTURE.md) ; script
  d'anonymisation des fixtures.

## 2026-11-19 — Fin de l'itération 0 : chaîne de dev complète

- **Objectif** : la page React affiche le statut de l'API via le proxy Vite,
  bout en bout (`GET /api/health` visible dans la page).
- **Fait** : proxy `/api` → back dans `vite.config.ts` ; `App.tsx` : fetch au
  montage du composant, contrôle `response.ok` avant désérialisation, contrat
  typé `HealthStatus`, état d'erreur rendu dans l'UI ; ménage du contenu de
  démo du template (assets, styles morts, favicon conservé) ; items de
  l'itération 0 cochés.
- **Appris** : une origine = schéma + hôte + port ; Same-Origin Policy (le JS
  d'une page ne peut lire que les réponses de sa propre origine) et pourquoi
  le proxy de dev l'esquive (la page ne parle qu'à Vite, qui relaie — CORS
  n'entre jamais en jeu) ; `fetch` tient sa promesse même sur 404/500 :
  `response.ok` détecte les erreurs HTTP, `catch` n'attrape que le réseau et
  les `throw` ; un `throw` dans un `then` descend la chaîne jusqu'au `catch`
  unique (`ok` est une valeur dérivée : statut entre 200 et 299).
- **Pièges résolus** : `ECONNREFUSED` côté Vite = proxy fonctionnel mais back
  éteint (lire une erreur à sa couche) ; 404 du favicon = bruit automatique
  du navigateur, pas une panne.
- **Décisions** : garde `if (!response.ok)` + code HTTP dans le message
  d'erreur ; type nommé `HealthStatus` à la frontière front ; en Conventional
  Commits, le reformatage est `refactor` (pas `chore`).
- **À revoir** : mécanique complète origine/SOP/CORS (intuition acquise,
  formulation à consolider) ; imports JS/TS et `defineConfig`.

## 2026-11-18 — Squelette du monorepo et premier endpoint

- **Objectif** : itération 0 — `src/Api` (ASP.NET Core minimal) + `src/Web`
  (Vite + React + TS strict), `GET /api/health` fonctionnel et testé.
- **Fait** : solution .NET 10 (`RLMatchTracker.slnx`, format XML devenu défaut
  du SDK — la commande `dotnet new sln` n'a pas changé de nom) ; endpoint
  health testé (200 + `{"status":"ok"}`) ; scaffold front ; synchronisation
  documentaire (ARCHITECTURE, ROADMAP, STACK, `.gitignore` vérifié).
- **Appris** : `.csproj` SDK-style (sdk `Web`, Nullable, ImplicitUsings) ;
  Minimal API : `MapGet` relie une route à une fonction, `TypedResults`
  explicite le statut et sérialise l'objet anonyme en JSON (contrat camelCase
  du web) ; config en cascade (`appsettings.Development.json`) ;
  `launchSettings.json` = ports et profils du dev local ; `npm install` =
  restore du monde JS (`package.json` demande, lock verrouille).
- **Pièges résolus** : scripts npm bloqués par la politique d'exécution
  PowerShell → `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ;
  `npm audit fix --force` rétrograderait Vite — à refuser.
- **Décisions** : health check en enveloppe JSON `{"status":"ok"}` (prête pour
  l'extension de l'itération 3) ; format `.slnx` assumé ; audit npm repoussé
  à l'itération 6.

## 2026-11-17 — Revue documentaire complète avant développement

- **Objectif** : relecture critique de la documentation (README, PRODUCT,
  ARCHITECTURE, CONTRIBUTING, ROADMAP), rituel de session, et fermeture de
  tous les points ouverts avant le code.
- **Fait** : revue complète du dossier, débattue point par point et
  intégrée : README finalisé ; règles d'accompagnement retravaillées
  (paliers d'aide sans chrono, review par transformations, critère de
  maîtrise, apprendre à chercher) ; identité du joueur local tranchée ;
  V2 redécoupée en itérations 5-9 ; PostgreSQL argumenté honnêtement ;
  date BakkesMod/EAC corrigée et sourcée ; tests et anonymisation des
  fixtures cadrés.
- **Appris** : vérifier les calendriers de support des outils avant de les
  figer en doc (.NET 8/9 en fin de support le 10 nov. 2026 → passage à
  .NET 10 LTS ; Node 26 est la LTS courante). L'API Stats n'émet aucun
  marqueur de « joueur local » : identification par PrimaryId configuré
  (Platform|Uid|Splitscreen) + validation au premier match. Un changement
  de schéma externe (Psyonix) doit s'arrêter à la frontière Ingestion ;
  seul un changement de champ métier traverse les couches.
- **Notions vues** : LTS vs STS, PrimaryId, provider-agnostic EF Core,
  fixtures anonymisées, statistiques par « playlist shape » (à vérifier
  en itération 1) ; feature folders et test « qu'est-ce qui change
  ensemble ? » ; DTO par frontière (flux vs API), dépendance
  unidirectionnelle vers le Domain, parseur comme traducteur isolant le
  cœur du schéma externe ; requêtes LINQ dans les handlers, `Data`
  fournit le vocabulaire ; handler Minimal API, `IQueryable` et
  exécution différée (le filtre s'exécute dans la base, pas en mémoire),
  `AsNoTracking`, `CancellationToken`, projection entité → DTO ; cache
  applicatif par clé de TanStack Query (staleness, invalidation) ;
  classes utilitaires Tailwind dans le JSX.
- **Décisions prises** : journal de session public (une entrée par session,
  diagnostic technique, notions vues consultables) ; l'auteur garde la main
  au clavier en toutes circonstances, la review produit des instructions de
  transformation ; JSON brut stocké par match dès l'itération 2 ; tests
  introduits à l'itération 5 puis obligatoires à chaque incrément ; ordre
  V2 : tests → CI → PostgreSQL → sessions → dashboard.
- **À revoir / prochaines étapes** : itération 0 (outils prêts : .NET 10,
  Node 26, VS Code) ; vérifier en itération 1 la fiabilité du champ
  playlist/mode sur fixtures réelles.
