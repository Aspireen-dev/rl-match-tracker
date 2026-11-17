# Stack technique — expliquée simplement

*Document en français. Une description simple de chaque outil du projet :
ce qu'il fait, et ce qu'il nous apporte ici. Le détail des décisions
d'architecture est dans `ARCHITECTURE.md`.*

## Back-end

### ASP.NET Core (.NET 10, C# 14)
Le framework web de Microsoft, la version moderne de ce qui s'appelait
ASP.NET à l'époque du .NET Framework. Ici, il héberge à la fois le
consommateur du flux du jeu (processus en arrière-plan) et l'API REST
que le front interroge. Version LTS : supportée jusqu'en 2028.

### Minimal APIs
La façon moderne d'écrire des endpoints dans ASP.NET Core : une route et
son traitement en un fichier, sans la cérémonie des controllers MVC.
Pour une API de quatre endpoints, c'est moins de code pour le même
résultat.

### BackgroundService
Un service d'arrière-plan hébergé par ASP.NET Core : du code qui tourne
en continu pendant toute la vie de l'application, indépendamment des
requêtes HTTP. Ici, c'est lui qui maintient la connexion TCP au jeu,
réceptionne le flux en permanence et le transmet au reste de l'application.

### System.Text.Json
Le désérialiseur JSON intégré à .NET : il transforme chaque message JSON
du jeu en objets C# typés. Configuré pour tolérer les champs inconnus,
pour survivre aux évolutions du flux.

### EF Core (Entity Framework Core)
Le mappeur objet-relationnel officiel de .NET : on décrit les tables en
classes C# (`Match`, `Player`...), EF Core génère le SQL, crée la base et
traduit les lectures en objets. Les migrations de schéma sont versionnées
dans le code, pas écrites à la main.

### SQLite
La base de données : un simple fichier sur disque, zéro installation,
zéro serveur. Amplement suffisant pour un historique de matchs local
(des milliers de lignes). Migration prévue vers PostgreSQL en V2 —
pour apprendre, pas par nécessité.

## Front-end

### React
La bibliothèque de référence pour construire des interfaces : on décrit
l'UI comme des fonctions (`composants`) qui transforment des données en
HTML, React se charge de mettre à jour l'écran quand les données
changent. Idiome moderne : composants fonctionnels + hooks uniquement.

### TypeScript
Du JavaScript avec des types vérifiés à la compilation. Le mode strict
transforme ces vérifications en vrai garde-fou : impossible d'appeler une
propriété possiblement absente sans l'avoir prouvé. Le but du projet
inclut de l'apprendre sérieusement, d'où le strict et l'interdiction
du `any`.

### Vite
L'outil de build et de serveur de développement du front : rechargement
instantané à chaque sauvegarde, et il fournit aussi le proxy de
développement qui redirige `/api/*` vers le back ASP.NET Core, évitant
tout problème de CORS en local.

### TanStack Query
Le gestionnaire d'état serveur : quand un composant a besoin de
données du back (liste des matchs, stats), TanStack Query gère le cycle
complet — chargement, erreur, mise en cache au niveau de l'application,
rafraîchissement arrière-plan. Retourner sur une page déjà visitée
s'affiche instantanément depuis le cache, sans refaire d'appel HTTP
inutile. Interdiction dans CONTRIBUTING : le fetching manuel via
`useEffect`.

### Tailwind CSS
Le style : des classes utilitaires prédéfinies directement dans le JSX
(`className="p-4 text-white rounded-lg"`), aucune classe CSS à nommer,
aucun fichier de style à maintenir. Échelles fixes (espacements,
tailles, palette) = rendu cohérent sans être designer.

### Recharts
La bibliothèque de graphiques : courbes de tendances, barres, aires.
Intégrée à React (on lui passe des données typées, elle rend le SVG).

### SignalR (V3)
La bibliothèque Microsoft de communication temps réel : le back pousse
des données vers le front sans que celui-ci demande. Servira pour la vue
live et l'overlay OBS. Différé en V3 : le produit doit d'abord prouver
sa couche données.

## Outils transverses

### Git + Conventional Commits
Le gestionnaire de versions, avec des messages normalisés
(`feat:`, `fix:`, `docs:`) qui rendent l'historique navigable et
générable en changelog. Pour un projet portfolio, l'historique est
une vitrine en soi.

### xUnit (V2)
Le framework de tests de référence du monde .NET moderne : chaque test
tourne dans une instance isolée, pas d'état partagé entre tests.

### Vitest + RTL (V2)
L'équivalent côté front : exécution de tests rapide (Vitest) et
manipulation des composants React comme le ferait un utilisateur
(React Testing Library).

### Docker + PostgreSQL (V2)
PostgreSQL : le serveur de base de données relationnelle répandu en
entreprise (multi-utilisateurs, réseau). Docker : l'outil qui l'empaquette
et l'exécute de façon identique partout. Introduits en V2 comme incrément
d'apprentissage assumé, avec transfert de l'historique existant.