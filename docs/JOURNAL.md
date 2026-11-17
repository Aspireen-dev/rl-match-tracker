# Journal de progression

*Une entrée par session de travail. Le "quoi" est coché dans ROADMAP.md,
le "comment" est documenté par le code : ce journal garde le pourquoi de
la progression — notions acquises, pièges résolus, décisions tranchées.*

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
  playlist/mode sur fixtures réels.