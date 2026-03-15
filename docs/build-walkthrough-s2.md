# Build Walkthrough — Scope 2 : Email Alerts + Scheduling

## Ce qu'on a fait

On a rendu ShipWatcher autonome. Plus besoin d'ouvrir le dashboard et de cliquer "Check All" — les verifications tournent toutes seules, et un email arrive si quelque chose casse.

C'est la difference entre un vigile qui fait ses rondes quand il y pense et un vigile qui a un planning fixe et qui appelle le proprietaire quand il trouve une porte ouverte.

## Les deux types d'emails

### 1. L'alerte immédiate

Quand un check echoue, un email part immediatement. Pas un email generique "quelque chose a plante" — un email precis :

- Quel projet a echoue
- Quel type de check (health ou smoke)
- Quel code d'erreur (HTTP 500, Timeout, etc.)
- Quand ca s'est passe

Le but : tu recois l'email, tu sais exactement quoi fixer, sans ouvrir le dashboard.

### 2. Le daily digest

Tous les matins a 8h UTC (10h heure Paris), un email resume avec tous les checks :

```
ShipWatcher: 11/11 checks passed

DocuQuery AI    health   ✓ 56ms
DocuQuery AI    smoke    ✓ 3667ms
WatchNext       health   ✓ 52ms
...
```

Pourquoi le daily digest ? Parce que "silence = tout va bien" ne rassure personne. Mehdi l'a demande apres 1 jour d'utilisation. Recevoir un email chaque matin avec "11/11 PASS" donne confiance que le systeme surveille vraiment — que ce n'est pas juste un script oublie dans un coin.

## Le scheduling : APScheduler vs cron externe

On avait deux options :

| Option | Comment ca marche | Avantage | Inconvenient |
|--------|-------------------|----------|--------------|
| **APScheduler (interne)** | Un planificateur de taches integre au serveur | Pas de cold start, tourne en continu | Consomme de la RAM en permanence |
| **Render Cron Job (externe)** | Render lance un script toutes les X heures | Pas de RAM gaspillee | Cold start a chaque execution (~30s), $1/mois |

On a choisi APScheduler. La raison : le cold start. Un cron externe doit demarrer le serveur, charger les dependances, et lancer les checks — 30 secondes perdues a chaque fois. Avec APScheduler, le serveur tourne deja, les checks partent instantanement.

Le scheduler a deux jobs :
- **Checks toutes les 6h** — configurable via la variable `CHECK_INTERVAL_HOURS`
- **Daily digest a 8h UTC** — configurable via `DIGEST_HOUR_UTC`

## L'integration Resend

Resend est un service d'envoi d'emails par API (Application Programming Interface — un moyen pour deux logiciels de se parler). Au lieu de configurer un serveur email complet (SMTP, DNS, SPF, DKIM — des heures de configuration), on envoie une requete a Resend et l'email part.

Le tier gratuit : 100 emails par jour. Pour 2 emails par jour (1 digest + eventuellement 1 alerte), c'est largement suffisant.

**Le piege :** Le premier email a atterri dans les spams. Les services d'email gratuits n'ont pas de reputation etablie — Gmail les classe automatiquement en spam. Pas un bloqueur pour un outil personnel (on sait ou chercher), mais a noter pour un eventuel V2 avec de vrais utilisateurs.

## La regle "no spam"

Un detail important : quand tous les checks passent, **aucun email d'alerte n'est envoye.** Seulement le daily digest. Si on envoyait un email "tout va bien" toutes les 6h, ca ferait 4 emails par jour de bruit — et au bout d'une semaine, on arreterait de les lire. Et le jour ou un vrai probleme arriverait, l'email serait noye dans le bruit.

C'est un principe classique du monitoring : **alerte uniquement sur l'anomalie.** Le daily digest existe pour rassurer. L'alerte existe pour agir.

## Le "Check All Now"

En plus du scheduling automatique, on a garde un endpoint `/trigger-check` pour lancer tous les checks manuellement. C'est le mode "pre-demo" : avant de partager son ecran, on clique, on attend 65 secondes, et on sait si tout marche.

65 secondes c'est long. La raison : les checks sont sequentiels (l'un apres l'autre). FeedbackSort a lui seul prend ~45 secondes (il classifie 2000 avis pour son smoke test). En V2, on pourrait paralleliser les checks pour descendre a ~15 secondes.

## Ce qu'on a appris

La valeur de ShipWatcher n'est pas dans les checks — c'est dans la **confiance.** Savoir que quelqu'un surveille, meme quand tu dors. Le daily digest a 8h du matin, c'est comme un gardien de nuit qui te laisse un post-it : "Tout etait calme cette nuit." Ca ne coute rien, mais ca change tout.
