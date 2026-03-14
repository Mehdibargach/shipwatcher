# Macro Retro — ShipWatcher

**Project:** ShipWatcher
**Version shipped:** V1
**Eval Gate decision:** GO (11/11 PASS)
**Date:** 2026-03-14

---

## 1. Harvest — What came out of the Eval Gate?

### Conditions (from GO — observations, not blockers)

| # | Observation | Level | Impact |
|---|------------|-------|--------|
| 1 | Check All prend 65s (FeedbackSort = 45s seul) | SIGNAL | UX — l'utilisateur attend longtemps sur le dashboard |
| 2 | Email arrive en spam la première fois | SIGNAL | L'utilisateur rate l'alerte la plus importante |
| 3 | Projets ajoutés via dashboard perdus au redeploy (seed.json = workaround) | SIGNAL | Pas viable pour un vrai produit multi-user |

### Build Learnings (from Build Log)

- **iCloud corrompt les repos git** — découvert 3 fois pendant le build. Les refs git sont dupliquées par la synchronisation iCloud. Solution : toujours recloner depuis GitHub, ne jamais faire confiance au repo local sur iCloud.
- **CORS est le premier bug de tout projet Lovable + FastAPI** — on a perdu 30 min à debugger un formulaire qui ne soumettait pas. Le problème était CORS, pas le frontend. Leçon : tester l'API directement via curl AVANT de debugger le frontend.
- **Le health check ne suffit JAMAIS** — DataPilot avait un service "Deployed" sur Render mais avec la mauvaise URL. WatchNext passait le health check mais avait un RateLimitError OpenAI. Le smoke test fonctionnel est non-négociable.
- **Render "Suspended" ≠ "Sleeping"** — confusion fréquente. Le plan $7/mo ne dort pas. Si un service est down, c'est un vrai problème (URL changée, billing, crash), pas un cold start.

### User/PM Signals (from wild tests, demos, feedback)

- **Mehdi a demandé le daily digest** — le "silence = tout va bien" n'était pas rassurant. Un résumé quotidien apporte de la confiance que le système veille.
- **"On rajoute ShipWatcher dans ShipWatcher?"** — le dogfooding est un excellent signal produit. Si le créateur l'utilise lui-même, le produit a de la valeur.
- **"C'est long"** — le spinner sans feedback temporel donne l'impression que ça freeze. Le compteur de secondes a résolu le problème. Leçon UX : toujours montrer de l'activité.
- **"Les features sans smoke test c'est pas acceptable"** — Mehdi a demandé que DocuQuery et FeedbackSort aient aussi des smoke tests. Un monitoring partiel ne rassure pas.

---

## 2. Decision — What do we do next?

**Decision : STOP**

**Why :** ShipWatcher remplit son objectif — Mehdi sait chaque matin si ses 6 projets marchent, et reçoit une alerte immédiate si quelque chose casse. Le produit est utilisé par son créateur quotidiennement (dogfooding). Les observations SIGNAL (latence 65s, spam, stockage) sont mineures et n'affectent pas la valeur core. Investir plus de temps sur ShipWatcher a un rendement décroissant — le temps est mieux investi sur le livre et le networking US.

**Si les conditions changent (ex: d'autres builders veulent l'utiliser) → ITERATE avec le Bridge ci-dessous.**

---

## 3. Bridge — Input for V2 (si ITERATE un jour)

### Problem Statement V2
- Les checks prennent trop longtemps (65s) — les utilisateurs pensent que le dashboard est figé
- Les projets ajoutés via dashboard sont perdus quand le serveur redéploie
- Les emails arrivent en spam — l'utilisateur rate les alertes critiques

### Riskiest Assumption V2
**"D'autres builders que moi vont configurer ShipWatcher et l'utiliser régulièrement (rétention > 1 semaine)."**

### Candidate Scopes V2
- Checks en parallèle (asyncio.gather) — latence 65s → ~15s
- SQLite sur Render Persistent Disk ($1/mo) — stockage durable
- Domaine email vérifié sur Resend — éviter les spams
- Historique des checks (timeline / graphe uptime)
- Auth simple (un mot de passe, pas de comptes)
- Landing page publique avec onboarding

---

## Completion

- [x] Eval Report reviewed
- [x] Decision documented with justification
- [x] Bridge section filled (si ITERATE un jour)
- [ ] Project Dossier
- [x] CLAUDE.md updated
