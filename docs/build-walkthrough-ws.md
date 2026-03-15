# Build Walkthrough — Walking Skeleton

## Ce qu'on a fait

On a construit le coeur de ShipWatcher : un systeme qui verifie si tes projets deployes marchent vraiment, pas juste s'ils sont allumes.

Imagine un vigile dans un immeuble. Il ne se contente pas de verifier que la lumiere est allumee dans chaque bureau (health check). Il ouvre la porte, regarde si quelqu'un travaille, et note ce qu'il voit (smoke test). ShipWatcher fait la meme chose pour tes applications web.

## Comment ca marche

```
Ajouter un projet (URL + endpoint)
    |
    v
Cliquer "Check Now"
    |
    v
ShipWatcher envoie une requete HTTP au projet
    |
    v
Le projet repond (ou pas)
    |
    v
Dashboard affiche: vert (OK) ou rouge (probleme) + temps de reponse
```

Le flow est volontairement simple. Un builder (un developpeur qui shippe des side projects) doit pouvoir ajouter un projet et voir son statut en moins de 2 minutes. Pas de configuration complexe, pas de dashboards a 15 onglets.

## Les briques techniques

Quatre fichiers, chacun avec un role precis :

1. **`api.py`** — Le serveur web. Il recoit les requetes du dashboard (ajouter un projet, lancer un check, voir les resultats). C'est le point d'entree de tout.

2. **`checker.py`** — Le moteur de verification. Il envoie des requetes HTTP (comme un navigateur) aux projets et analyse les reponses. Deux types de checks : health (le serveur repond ?) et smoke (la feature marche ?).

3. **`store.py`** — Le stockage. Les projets sont sauvegardes dans un fichier JSON. Pas besoin de base de donnees pour 10-50 projets — un fichier suffit.

4. **`seed.json`** — Les projets pre-configures. Les 6 side projects du portfolio (DocuQuery, WatchNext, DataPilot, FeedbackSort, EvalKit, ShipWatcher lui-meme) sont pre-charges au demarrage.

## Ce qui a marche du premier coup

- **Le CRUD projets** — ajouter, modifier, supprimer un projet fonctionne immediatement. FastAPI genere automatiquement la validation des donnees.
- **Le health check** — un GET sur `/health` avec un timeout de 30 secondes. Simple et fiable.
- **La validation d'URL** — les URLs malveillantes (`javascript:alert(1)`, URLs vides) sont rejetees avant d'atteindre le moteur de check.
- **Le setup time** — moins d'une minute pour ajouter un projet et voir son statut. Bien en dessous de la cible de 2 minutes.

## Ce qui a necessite une decision

### JSON fichier vs base de donnees

On aurait pu utiliser SQLite (une base de donnees legere) ou PostgreSQL (une vraie base de donnees). Mais pour un outil personnel qui monitore 6 projets, un fichier JSON est largement suffisant.

Les avantages : zero configuration, zero dependance, le fichier est lisible a l'oeil nu, on peut le modifier a la main si besoin. L'inconvenient : si deux requetes ecrivent en meme temps, on pourrait perdre des donnees. Mais avec un seul utilisateur et 6 projets, ca n'arrivera pas.

**La regle :** On prend la solution la plus simple qui marche. On complexifie seulement si un probleme reel apparait.

### httpx async vs requests

Le moteur de check utilise `httpx` (une librairie HTTP pour Python) en mode asynchrone. Ca veut dire qu'on peut envoyer plusieurs requetes en meme temps sans attendre que chacune finisse avant de lancer la suivante.

Pourquoi c'est important : si on monitore 6 projets et que chacun met 2 secondes a repondre, en mode synchrone ca prendrait 12 secondes. En mode async, ca prend 2 secondes (toutes les requetes partent en parallele).

## Le Skeleton Check

La question du Walking Skeleton etait : **"Un solo builder va-t-il configurer des endpoints de test ET verifier les resultats regulierement — le tout en moins de 2 minutes de setup ?"**

Reponse : **OUI.** Le setup prend moins d'une minute. Le dashboard est clair. Le builder voit immediatement si ses projets marchent.

On continue vers le Scope 1 : les smoke tests fonctionnels.
