# Project Dossier — ShipWatcher

> Template from The Builder PM Method — post-SHIP

---

**Project Name:** ShipWatcher
**One-liner:** Never demo a dead product again — monitoring automatique pour builders qui shippent.
**Live URL:** https://shipwatcher.onrender.com
**GitHub:** https://github.com/Mehdibargach/shipwatcher
**Date Shipped:** 2026-03-14
**AI Typology:** Monitoring / Observability (#6 Builder PM portfolio)

---

## 1-Pager Summary

**Problem :** Tu as 6 side projects deployes. Un recruteur te demande une demo. Tu partages ton ecran, tu cliques... et ca plante. Le serveur est eteint, la cle API a expire, ou le service cloud a change l'URL. Tu ne le savais pas parce que tu ne vérifies jamais manuellement tes 6 projets chaque matin.

**User :** Solo builders et indie devs avec 3-10 projets deployes (Render, Vercel, Railway). Des gens qui shippent mais qui n'ont pas le temps de monitorer. Aussi : freelancers qui maintiennent des projets clients, Builder PMs, vibe coders.

**Solution :** Ajouter tes projets (URL + endpoint de test) en 1 minute. ShipWatcher vérifie automatiquement toutes les 6h — pas juste un ping, une vraie requete fonctionnelle (smoke test). Si ca casse, email d'alerte immediat. Chaque matin a 8h, un daily digest avec le statut de tous tes projets.

---

## Architecture

```
Frontend (Lovable — React + Tailwind)
    |
    v
Backend (FastAPI — Python — Render)
    |
    ├── checker.py — Health checks (GET /health) + Smoke tests (POST /endpoint)
    ├── scheduler.py — APScheduler (checks 6h + keep-alive 10min + digest 8h UTC)
    ├── alerts.py — Emails via Resend API
    └── store.py — Stockage JSON fichier (seed.json au boot)
```

**Stack :** FastAPI + httpx async + APScheduler + Resend + Lovable + Render ($7/mois)

---

## Key ADRs

| Decision | Choix | Alternative rejetee | Pourquoi |
|----------|-------|-------------------|----------|
| Stockage | JSON fichier | SQLite, PostgreSQL | 10-50 projets max, zero config, lisible a l'oeil, modifiable a la main |
| Scheduling | APScheduler interne | Render Cron Job ($1/mois) | Pas de cold start, tourne en continu dans le meme process |
| Email | Resend API | SendGrid, SMTP custom | 100 emails/jour gratuit, API simple, 3 lignes de code |
| Smoke test engine | httpx async | requests (sync) | Checks en parallele — 6 projets en 2s au lieu de 12s |
| Persistence | seed.json (commite) | Base de donnees | Projets du portfolio sont fixes, survivent aux redeploys sans DB |

---

## Eval Results

| # | Critere | Level | Seuil | Resultat | Status |
|---|---------|-------|-------|----------|--------|
| G1 | Detection UP correcte | BLOCKING | 100% | 100% (3/3 runs) | **PASS** |
| G2 | Detection DOWN correcte | BLOCKING | 100% | 100% | **PASS** |
| G3 | Smoke distingue health vs feature | BLOCKING | Detecte feature fail quand serveur UP | Detecte | **PASS** |
| G4 | Email alerte delivre | BLOCKING | Email dans inbox | Recu | **PASS** |
| G5 | Daily digest delivre | QUALITY | Email avec tableau complet | Recu, format correct | **PASS** |
| G6 | Zero faux positifs | BLOCKING | 0 faux positifs en 3 runs | 0/3 | **PASS** |
| G7 | Securite URL | BLOCKING | XSS + vides rejetes | Rejetes | **PASS** |
| G8 | Seed data survit au redeploy | QUALITY | 6 projets apres redeploy | 6/6 | **PASS** |
| G9 | Setup time | QUALITY | < 2 min | < 1 min | **PASS** |
| G10 | Check All latence | SIGNAL | < 120s | 64.9s | **PASS** |
| G11 | No spam quand tout OK | QUALITY | 0 email inutile | 0 | **PASS** |

**Decision : GO → SHIP** (11/11 PASS)

---

## What I Learned

1. **Technical :** iCloud et git ne font pas bon menage. iCloud cree des fichiers dupliques ("fichier 2") qui corrompent les refs git. Solution : `.gitignore` pour les doublons + toujours verifier les refs apres un push. En V2 : deplacer les repos hors d'iCloud.

2. **Product :** Un health check ne suffit jamais. Plusieurs projets du portfolio passaient le health check mais etaient en realite casses (mauvaise URL, cle API expiree, rate limit). Le smoke test fonctionnel — une vraie requete comme un utilisateur — est la seule facon de savoir si ca marche.

3. **Process :** "Silence = tout va bien" ne rassure personne. Le daily digest a ete demande apres 1 jour d'utilisation. La confiance vient de la preuve positive ("11/11 PASS ce matin"), pas de l'absence de mauvaise nouvelle.

4. **Infra :** Render "Zero Downtime" = zero downtime *pendant un deploy*, pas "service toujours allume." Le Starter tier ($7/mois) met en veille apres 15 min d'inactivite. Solution : keep-alive ping toutes les 10 min depuis ShipWatcher, ce qui permet de passer les autres services en Free tier ($0). Economie : ~$35/mois.

---

## Post-SHIP Iterations

### Iteration 1 (2026-03-15) — Keep-Alive + Error Handling

**Declencheur :** ShipWatcher a detecte son premier vrai probleme — FeedbackSort smoke test HTTP 500.

**Root cause :** Cold start Render (~30-50s) + traitement FeedbackSort (~46s) = ~90s, pile a la limite du timeout.

**Corrections :**
- FeedbackSort : error handling sur appels OpenAI + timeout 30s
- ShipWatcher : timeout smoke 90s → 180s
- ShipWatcher : keep-alive ping toutes les 10 min (health-only, zero credit API)
- ShipWatcher : `.gitignore` pour les doublons iCloud

**Impact :** Les 5 autres services peuvent passer en Free tier. Economie ~$35/mois.

---

## Content Extracted

- [x] Book chapter : Ch.8 (Monitoring typology — pourquoi shipper sans monitorer c'est comme conduire sans retro)
- [ ] LinkedIn post : "My side project caught a bug in my other side project" / "Health check passed, feature was broken — why smoke tests matter"
- [ ] Newsletter : ShipWatcher build story (de "je demo un produit mort" a "11/11 PASS chaque matin")
- [x] STAR story : "Built an automated monitoring tool that watches 6 AI products 24/7. It caught its first real bug within 24 hours of shipping — a cold start timeout that would have crashed a live demo. The fix also saved $35/month by enabling Free tier migration with keep-alive pings."
