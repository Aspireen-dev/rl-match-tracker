# Journal de progression

*Une entrée par session de travail. Le "quoi" est coché dans ROADMAP.md,
le "comment" est documenté par le code : ce journal garde le pourquoi de
la progression — notions acquises, pièges résolus, décisions tranchées.*

## 2026-11-28 — Mini-audit sécurité avant itération 2 : 5 points traités

- **Objectif** : auditer la sécurité du code et des données avant de passer à l'itération 2 (modèle EF Core + persistance), et traiter chaque point trouvé.
- **Constat initial** : aucun secret dans le code ni dans l'historique git ; les captures brutes (vrais noms + IDs Steam/Epic de joueurs tiers) sont bien gitignorées et jamais commitées ; la fixture commitée est propre (vérifié au scanner). Côté surface HTTP : un seul endpoint `GET /api/health`, Kestrel en localhost uniquement, aucune donnée entrante — rien à corriger pour un outil 100 % local.
- **Point 1 — PII dans les logs (corrigé)** : `StreamEventParser` logguait noms de joueurs et `PrimaryId` en `Information`. Règle appliquée : noms/IDs UNIQUEMENT en `LogDebug` (actif en Development seulement) ; `PrimaryId` plus jamais loggué ; le nom d'équipe n'est plus loggué (un nom d'équipe PEUT être le pseudo d'un joueur, ex. « LOVERBHOOYS ») ; le preview de JSON invalide tronqué de 200 à 80 caractères. **Vérifié** : replay de la fixture en Production → 0 nom/ID dans les logs, tout en ayant bien consommé le flux.
- **Point 2 — scripts de capture gitignorés (corrigé)** : `captures/` ignorait tout le dossier, y compris les outils (`capture_stream.py`, etc.) cités dans ce journal. `.gitignore` passé à `captures/*` + `!captures/*.py` : les scripts sont commités, les `*.jsonl` bruts non.
- **Point 3 — anonymiseur par liste de champs (corrigé)** : `tests/anonymize_fixture.py` détecte maintenant aussi PAR PATTERN (toute string en `Platform|uid|Splitscreen` ou GUID 32 hex, quel que soit le champ) + noms de champs insensibles à la casse. **Nouveau** : `tests/check_fixtures_privacy.py`, scanner qui bloque toute fixture contenant un vrai nom/UID/GUID, lancé à chaque commit via le hook `.githooks/pre-commit` (`git config core.hooksPath .githooks`). **Vérifié** : scanner OK sur la fixture commitée et sur une ré-anonymisation, FUITE (rc=1) sur les 7 captures brutes.
- **Point 4 — confiance au flux local (garde-fou ajouté)** : n'importe quel process local peut usurper le jeu sur 127.0.0.1:49123. Ajout d'un plafond de payload (1 M caractères) dans `ParseData<T>` : au-delà, warning + ignore, le flux continue. **Vérifié** : replay d'un payload de 1,5 M chars → `Oversized event payload ignored: 1500053 chars (max 1000000)`.
- **Point 5 — `AllowedHosts: "*"`, pas de CORS/auth (inchangé, assumé)** : acceptable tant que tout reste en localhost (documenté dans CONTRIBUTING : « No authentication (local app) »). À revisiter si l'API est un jour exposée au-delà de la machine ou si un endpoint accepte des données.
- **Décision** : itération 2 (persistance EF Core) peut démarrer sur une base assainie. Rappel : les futures BDD locales (`*.db`, `*.sqlite`) sont déjà gitignorées.

## 2026-11-26 — Itération 1, session 5 : script d'anonymisation des fixtures (itération 1 terminée)

- **Objectif** : anonymiser les captures brutes en fixtures commitables (dernier item itération 1).
- **Fait** : `tests/anonymize_fixture.py` — capture JSONL brute → fixture anonymisée dans
  `tests/Api.Tests/Fixtures/`. Noms → `Player_XX` (mapping cohérent dans tout le fichier),
  `PrimaryId` → `Platform|uid factice|Splitscreen` (format préservé : numérique Steam-like,
  hex 32 pour Epic), `MatchGuid` → GUID factice 32 hex. Le reste (scores, stats, Arena,
  PlaylistId, Loadout) est conservé ; noms d'équipe génériques Blue/Orange gardés.
- **Vérifié** : fixture `match-casual-2v2.anonymized.jsonl` (13 346 msg) — 0 nom/UID réel
  restant, formats OK, et le parser C# la lit sans erreur (replay + API : 0 warning).
- **Décision** : ce script est le seul chemin capture brute → fixture commitée (chemin réel
  noté dans CONTRIBUTING.md).
- **🚀 Itération 1 terminée** : prochaine = itération 2 (modèle EF Core + persistance des matchs).

## 2026-11-26 — Itération 1, session 4 : corrélation PlaylistId sur 4 matchs réels

- **Objectif** : vérifier la fiabilité du champ playlist/mode (risque ARCHITECTURE.md).
- **Fait** : 4 nouvelles captures (sonde `capture_stream.py`, jeu allumé) : ranked 3v3
  (11 915 msg), Hoops (13 063 msg), ranked 2v2 (12 479 msg), Rumble (5 867 msg, forfeit 4-0
  capturé quand même). Extraction via `captures/extract_playlist.py`.
- **Résultat** : `PlaylistId` constant sur tout un match et distinct par mode —
  casual 2v2=2, ranked 2v2=11, ranked 3v3=13, Hoops=27 (Arena HoopsStadium_P),
  Rumble=28 (Arena Labs_DoubleGoal_V2_P). Deux extra modes testés → chacun son propre ID.
  → ranked vs casual DISTINGUABLE par PlaylistId ; le plan B « playlist shape » n'est
  pas nécessaire. Psyonix ne publie pas la table officielle des IDs : le mapping observé
  est à compléter au fil des matchs.
- **Décision** : risque playlist/mode d'ARCHITECTURE.md marqué résolu ; on s'appuie sur
  `Game.PlaylistId` (+ `Game.Arena` pour les extra modes). Table de correspondance
  compilée dans `docs/PLAYLISTS.md` (nos captures + table communautaire publique ;
  LTM = IDs rotatifs → fallback Arena / "Playlist #ID").
  Le mapping C# (affichage) sera créé à l'itération 3 (YAGNI) ; le PlaylistId brut est
  toujours stocké.
- **Reste itération 1** : script d'anonymisation des fixtures. Puis itération 2 (persistance).

## 2026-11-25 — Itération 1, session 3 : DTOs typés + parseur, validés par replay de capture

- **Objectif** : désérialiser le flux en DTOs typés (UpdateState + événements), avec
  tolérance aux champs inconnus.
- **Fait** : 13 DTOs dans `src/Api/Ingestion/Dtos/` raccordés à la doc officielle (champs
  CONDITIONAL/SPECTATOR → nullable ; `Assister` ajouté sur GoalScored) et aux captures
  réelles. `StreamEventParser` (frontière du schéma externe) : enveloppe `StreamEnvelope`
  puis double désérialisation de `Data` (string JSON échappée — divergence doc/wire notée
  dans ARCHITECTURE), dispatch par constantes `StreamEvents`, résultat `ParsedStreamEvent`
  (record). Tolérance centralisée dans `ParseData<T>` : guard null/vide + catch JsonException
  → warning tronqué + null, le flux continue. Service réduit au transport (connexion,
  boucle, backoff) ; parser enregistré en singleton (DI). Filtre log `Api.Ingestion: Debug`
  en Development.
- **Vérifié sans le jeu** : `captures/replay_capture.py` rejoue `match-casual-2v2.jsonl`
  sur TCP 49123 (faux jeu) → 13 346 messages parsés, 0 warning, 0 JSON invalide ; logs
  lisibles (UpdateState #300 avec PlaylistId=2, Arena, score ; buts avec buteur).
- **Refactor** : parsing extrait du service vers `StreamEventParser` (testable avec les
  fixtures à l'itération 5) ; re-vérifié par replay, logs identiques.
- **Appris** : record positionnel (égalité par valeur, utile pour les tests) ;
  `where T : class` autorise le `return null` des méthodes génériques ; System.Text.Json
  ignore les champs JSON inconnus par défaut ; un warning CS8604 n'est pas du bruit
  (ArgumentNullException hors du catch → guard clause) ; `dotnet run --no-launch-profile`
  = environnement Production (appsettings.Development.json non chargé).
- **Prochaines étapes** : corréler `PlaylistId` sur casual 3v3 + extra mode (risque
  ARCHITECTURE.md) ; script d'anonymisation des fixtures ; puis itération 2 (persistance).

## 2026-11-23 — Itération 1, session 2 : captures réelles du flux Stats API

- **Objectif** : capturer des échantillons JSON réels du flux et les stocker comme
  base des futurs tests (captures brutes dans `captures/`, gitignoré).
- **Fait** : sonde one-off Python (`captures/capture_stream.py`) qui découpe le flux
  concaténé (objets JSON sans séparateur) via `raw_decode` en JSONL, et
  `captures/inspect_stream.py` pour l'inventaire. 3 captures : menu (572 msg/30 s),
  entraînement solo (353 msg), match casual 2v2 complet (13 346 msg, 41 Mo, MatchGuid
  FAD7CC7A…, score 3-2 confirmé, 0 ligne illisible).
- **Piège** : flux arrêté (port 49123 ouvert, 0 paquet émis) alors que le ini contenait
  Port/PacketSendRate. Doc officielle : `PacketSendRate` (défaut 0 = off) active l'API et
  le ini n'est lu qu'au lancement du jeu → redémarrage obligatoire après modif.
  `bEnabled=1` ajouté en même temps que le redémarrage (clé UE3 legacy, non documentée
  par Psyonix) : les deux variables ont changé simultanément, test A/B prévu en prochaine
  session pour savoir lequel des deux a rétabli le flux.
- **Découverte clé (format)** : enveloppe `{"Event","Data"}`, `Data` = JSON échappé
  (double désérialisation). `UpdateState.Data = {MatchGuid, Players[], Game}` avec
  `Game.PlaylistId`, `Game.Arena`, `Game.Teams[].Score` ; `Player.PrimaryId` au format
  `Platform|Uid|Splitscreen`. Chaque but émet 2 `GoalScored` (un réel, un vide
  GoalTime=0 pendant le replay) → compter les buts via `StatfeedEvent EventName='Goal'`
  ou `Teams[].Score`.
- **Décisions** : captures brutes dans `captures/` (CONTRIBUTING) ; aucun filtrage à la
  capture (brut intégral, rejouable) — la sélection des champs se fera dans les DTOs.
- **Prochaines étapes** : DTOs typés (UpdateState + événements, tolérance champs
  inconnus) écrits contre ces captures ; corréler `PlaylistId` sur casual 3v3 + extra
  mode (risque ARCHITECTURE.md) ; script d'anonymisation des fixtures.

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
