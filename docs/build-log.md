# BUILD LOG — ShipWatcher

## Walking Skeleton — 2026-03-14

**Objectif :** Verifier qu'un builder peut ajouter un projet, lancer un check, et voir le resultat (vert/rouge) en moins de 2 minutes.

**Ce qui a ete construit :**
- `api.py` — Backend FastAPI avec CRUD projets + endpoints de check
- `checker.py` — Moteur de checks async (health check + smoke test fonctionnel)
- `store.py` — Stockage JSON fichier (pas besoin de base de donnees pour 10-50 projets)
- `seed.json` — 6 projets pre-configures (DocuQuery, WatchNext, DataPilot, FeedbackSort, EvalKit, ShipWatcher)

**Resultats : 5/5 PASS**

| Test | Critere | Resultat |
|------|---------|----------|
| WS-1 | Ajouter un projet valide | Projet dans la liste avec nom + URL |
| WS-2 | Check projet UP (DocuQuery) | Status=PASS, latence 56ms |
| WS-3 | Check projet DOWN (fausse URL) | Status=FAIL, erreur affichee |
| WS-4 | URL adversariale (javascript:alert) | Rejetee avant le backend |
| WS-5 | Setup time < 2 min | < 1 min |

**Skeleton Check : OUI** — Un builder peut ajouter et checker un projet en moins d'une minute.

**Decision cle :** Stockage JSON fichier plutot que SQLite ou Postgres. Pour 10-50 projets, un fichier JSON suffit largement. Pas besoin d'installer une base de donnees pour un outil de monitoring personnel.

**Temps passe :** ~2h

**Next step :** Scope 1 — smoke tests fonctionnels (pas juste un ping, une vraie requete).

---

## Scope 1 : Smoke Tests Fonctionnels — 2026-03-14

**Objectif :** Au-dela du simple "le serveur repond", verifier que les features marchent vraiment. Un smoke test envoie une vraie requete (comme un utilisateur le ferait) et valide la reponse.

**Ce qui a ete construit :**
- `checker.py` enrichi — smoke test : POST avec payload configurable (JSON ou form data) + validation d'un champ dans la reponse
- `seed.json` enrichi — 5 projets avec smoke test configure (DocuQuery `/query`, WatchNext `/recommend`, DataPilot `/analyze`, FeedbackSort `/classify`, EvalKit `/demo`)
- Support JSON + form data — certains projets (FeedbackSort, DataPilot) utilisent des formulaires, pas du JSON

**Resultats : 5/5 PASS**

| Test | Critere | Resultat |
|------|---------|----------|
| S1-1 | Configurer smoke test WatchNext | Config sauvee, visible dans le projet |
| S1-2 | Smoke test PASS (WatchNext) | `movies` present dans la reponse |
| S1-3 | Smoke test FAIL (champ inexistant) | Dashboard distingue "serveur UP mais feature cassee" |
| S1-4 | Health + smoke ensemble | 2 resultats separes par projet |
| S1-5 | Support form data (FeedbackSort) | POST /classify avec form data fonctionne |

**Bug corrige :** CORS entre Lovable (frontend) et FastAPI (backend). Premiere tentative de soumission de formulaire bloquee. Le navigateur envoie un preflight OPTIONS que FastAPI ne gerait pas. Fix : middleware CORS avec origins Lovable + localhost.

**Apprentissage cle :** Un health check ne suffit jamais. DataPilot avait "Deployed" sur Render mais une mauvaise URL. WatchNext passait le health check mais avait un RateLimitError OpenAI sur les requetes reelles. Le smoke test fonctionnel est non-negociable.

**Temps passe :** ~2h

**Next step :** Scope 2 — alertes email + scheduling automatique.

---

## Scope 2 : Email Alerts + Scheduling — 2026-03-14

**Objectif :** Plus besoin de checker manuellement. Les checks tournent automatiquement toutes les 6h, et un email part si quelque chose casse.

**Ce qui a ete construit :**
- `scheduler.py` — APScheduler avec 2 jobs : checks toutes les 6h + daily digest a 8h UTC
- `alerts.py` — Emails via Resend API : alerte sur echec + daily digest complet
- `api.py` enrichi — endpoints `/trigger-check` et `/trigger-digest` pour tests manuels
- Envvars : `RESEND_API_KEY`, `ALERT_EMAIL`

**Resultats : 5/5 PASS**

| Test | Critere | Resultat |
|------|---------|----------|
| S2-1 | Email alerte sur echec | Email recu avec nom du projet + erreur + timestamp |
| S2-2 | Zero email quand tout OK | Logs : "All checks passed — no alert needed" |
| S2-3 | Cron tourne automatiquement | 2+ executions en 2 min (intervalle test) |
| S2-4 | Daily digest | Email avec tableau complet 11 checks |
| S2-5 | Pre-demo mode (Check All) | Tous les resultats rafraichis < 65s |

**Decision cle :** APScheduler interne plutot que Render Cron Job. Un cron externe ($1/mois) lance un cold start a chaque execution. Un scheduler interne tourne en continu dans le meme process — pas de cold start, pas de cout supplementaire.

**Apprentissage cle :** "Silence = tout va bien" ne rassure personne. Le daily digest a ete demande par Mehdi apres 1 jour d'utilisation. Recevoir un email chaque matin avec "11/11 PASS" donne confiance que le systeme surveille vraiment.

**Temps passe :** ~2h

**Next step :** Scope 3 — dashboard polish + deploy.

---

## Scope 3 : Dashboard + Deploy — 2026-03-14

**Objectif :** Dashboard visuel clair, deploy sur Render, demo-ready.

**Ce qui a ete construit :**
- Frontend Lovable (React + Tailwind) — dashboard avec statuts, couleurs, derniere verification
- Seed data persistence — `seed.json` charge au boot pour survivre aux redeploys
- Deploy Render — backend live sur `https://shipwatcher.onrender.com`

**Resultats : 6/6 PASS**

| Test | Critere | Resultat |
|------|---------|----------|
| S3-1 | Clarte en 10s | "Ca monitore mes projets" compris immediatement |
| S3-2 | Statuts visuels | Vert = UP, Rouge = DOWN, "last checked" visible |
| S3-3 | Supprimer un projet | Disparait, checks s'arretent |
| S3-4 | Deploy fonctionne | URL publique accessible, checks fonctionnels |
| S3-5 | Mobile responsive | Lisible sur telephone, pas de scroll horizontal |
| S3-6 | Modifier un projet | Nouvelle URL utilisee au prochain check |

**Bug corrige :** Projets ajoutes via le dashboard perdus au redeploy Render. Le stockage JSON est ephemere (le filesystem Render est reinitialise a chaque deploy). Fix : `seed.json` commite dans le repo, charge au premier boot. Les projets de base survivent toujours.

**Temps passe :** ~2h

**Next step :** Evaluation formelle → SHIP.

---

## Post-SHIP : Keep-Alive + Error Handling — 2026-03-15

**Objectif :** Corriger le HTTP 500 detecte par ShipWatcher sur FeedbackSort, et ajouter un keep-alive pour eviter les cold starts.

**Contexte :** ShipWatcher a detecte son premier vrai probleme en production — FeedbackSort smoke test renvoyait HTTP 500. Root cause : cold start Render Starter (~30-50s) + temps de classification FeedbackSort (~46s) = ~90s, pile a la limite du timeout.

**Ce qui a ete fait :**

1. **FeedbackSort — Error handling** (commit sur feedbacksort)
   - Try/except autour de l'appel OpenAI + json.loads()
   - Timeout explicite 30s sur les appels OpenAI
   - HTTP 503 avec message clair au lieu d'un 500 brut

2. **ShipWatcher — Timeout augmente** (commit `2b1dc8d`)
   - Smoke test timeout : 90s → 180s
   - Marge suffisante pour cold start + traitement

3. **ShipWatcher — Keep-alive ping** (commit `ef81a4b`)
   - Nouveau job : GET /health sur tous les services toutes les 10 min
   - Health-only — pas de smoke test, zero credit API consomme
   - Permet de passer les autres services en Free tier ($0) sans cold start

4. **ShipWatcher — Fix iCloud** (commit `a1da36c`)
   - iCloud creait des doublons ("fichier 2") qui cassaient les refs git
   - Fichiers restaures + `.gitignore` pour bloquer les doublons

**Apprentissage cle :** Render "Zero Downtime" = zero downtime *pendant un deploy*, pas "service toujours allume". Le Starter tier met en veille apres 15 min d'inactivite. iCloud et git ne font pas bon menage — les fichiers dupliques cassent les refs.

**Impact financier :** Les 5 autres services peuvent passer en Free tier. ShipWatcher (Starter $7) les garde eveilles. Economie : ~$35/mois.

**Temps passe :** ~1h30
