# Builder PM 1-Pager

> Template from The Builder PM Method — FRAME phase

---

**Project Name:** ShipWatcher
**One-liner:** Never demo a dead product again — monitoring automatique pour les builders qui shippent.
**Date:** 2026-03-14
**Builder PM Method Phase:** Developer Tooling / Observability (6ème typologie)

---

## Problem

- **P1 — Tu découvres les pannes EN LIVE.** Tu fais une démo devant un recruteur ou un client. Le backend est down, l'API a atteint sa limite, le service a été suspendu. Tu le découvres au moment le plus gênant. Zéro alerte avant.
- **P2 — Un ping HTTP ne suffit pas.** Ton backend peut répondre 200 sur `/health` mais planter dès qu'un utilisateur envoie une vraie requête. Le health check classique ne teste pas les features — il teste que le serveur est allumé.
- **P3 — Les outils de monitoring ne sont pas faits pour toi.** Datadog, UptimeRobot, Betterstack : ce sont des outils d'infra pour des SREs en entreprise. Trop de config, trop cher, trop complexe pour un builder solo avec 5 side projects sur Render.
- **P4 — Tu ne sais pas AVANT une démo si tout marche.** Pas de bouton "vérifier que tout est OK" avant de partager ton écran.

**Ce qui existe aujourd'hui :** UptimeRobot (gratuit mais ping seulement), Betterstack ($25+/mo, trop complexe), scripts manuels (personne ne les maintient).

**Pourquoi c'est cassé :** Ces outils répondent à la question "mon serveur est-il up ?". Les builders ont besoin de la réponse à : "mon produit marche-t-il vraiment ?"

## User

- **Primary :** Builders solos / indie devs qui ont 3-10 side projects déployés (Render, Vercel, Railway)
- **Secondary :** Freelances qui maintiennent des projets clients, Builder PMs, vibe coders
- **Context :** Le pain survient quand tu fais une démo (entretien, meeting client, post LinkedIn) et que tu réalises que ton produit est cassé. Fréquence : chaque fois que tu n'as pas vérifié manuellement avant — donc régulièrement.

## Solution

> Chaque pain est mappé à une feature qui le résout.

| Pain | Feature |
|------|---------|
| P1 — Découvrir les pannes en live | **Alertes email automatiques** quand un check fail (quotidien) |
| P2 — Un ping ne suffit pas | **Smoke tests fonctionnels** : envoie une vraie requête, valide la structure de la réponse |
| P3 — Outils trop complexes | **Dashboard simple** : colle ton URL + un endpoint de test, c'est parti en 2 min |
| P4 — Pas de vérification pré-démo | **Mode pre-demo** : un bouton "check all now", réveille les backends + smoke test |

## Riskiest Assumption

> L'hypothèse qu'on teste avec le MVP :

**"Un builder solo va configurer ses endpoints de test (pas juste un ping) ET consulter les résultats assez régulièrement pour que le monitoring ait de la valeur — le tout en moins de 2 minutes de setup."**

Contraintes non-fonctionnelles : le setup doit prendre < 2 min par projet, le dashboard doit charger en < 3s, les alertes doivent arriver dans les 5 min après détection d'un problème.

## Scope Scoring

| Feature | Pain | Risk | Effort | Score | In/Out |
|---------|------|------|--------|-------|--------|
| Health check multi-projets (ping /health) | 2 | 1 | 1 | **2** | OUT (trop basique seul) |
| Smoke test fonctionnel (vraie requête + validation réponse) | 3 | 3 | 2 | **4** | **IN** |
| Dashboard web (statut de tous les projets) | 3 | 2 | 2 | **3** | **IN** |
| Alertes email (notification quand un check fail) | 3 | 2 | 1 | **4** | **IN** |
| Mode pre-demo (warmup + check all) | 2 | 2 | 1 | **3** | **IN** |
| Config via formulaire web (ajouter un projet en cliquant) | 2 | 3 | 2 | **3** | **IN** |
| Historique des checks (timeline) | 1 | 1 | 2 | **0** | OUT |
| Intégration Slack | 1 | 1 | 2 | **0** | OUT |
| Multi-user / auth | 1 | 1 | 3 | **-1** | OUT |

### MVP (Score >= 3)
- Smoke test fonctionnel (vraie requête + validation réponse)
- Dashboard web (statut live de tous les projets)
- Alertes email automatiques
- Mode pre-demo (warmup + check all now)
- Config via formulaire web (ajouter/modifier un projet)

### Out of Scope (Score < 3)
- Health check seul (trop basique, le smoke test le couvre)
- Historique des checks / timeline
- Intégration Slack
- Multi-user / authentification

## Success Metrics

| Metric | Target | How to Test |
|--------|--------|-------------|
| Setup time par projet | < 2 min | Chronomètre : de "j'arrive sur le dashboard" à "mon projet est monitoré" |
| Détection de panne | 100% des pannes simulées | Couper un backend Render, vérifier que l'alerte part |
| Faux positifs | 0 sur 7 jours | Monitorer mes 5 projets pendant 1 semaine, compter les fausses alertes |
| Smoke test accuracy | Le smoke test fail ssi le produit est réellement cassé | Tester avec un backend down, un backend qui timeout, un backend qui renvoie une erreur |

## Key Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend framework | FastAPI (Python) | Cohérent avec les 5 autres projets, même stack, même déploiement Render |
| Frontend | React + Tailwind (Lovable) | Même stack que les 5 projets, vitesse de livraison |
| Stockage projets | JSON file ou SQLite | Pas besoin de Postgres pour 10-50 projets. Simplicité. |
| Scheduling des checks | Cron interne (APScheduler) ou Render Cron Job | Pas besoin de GitHub Actions pour un produit SaaS — le cron tourne sur le backend lui-même |
| Alertes email | Resend ou SendGrid (free tier) | API simple, 100 emails/jour gratuits, suffisant pour le MVP |
| Smoke test engine | httpx async + validation JSON configurable | Réutilise exactement le code du prototype monitor.py qu'on a déjà |

## Open Questions

- **Rabbit Hole #1 — Comment l'utilisateur configure un smoke test ?** Un health check c'est simple (URL + GET). Mais un smoke test fonctionnel a besoin d'un endpoint, d'un payload, et d'une règle de validation. Comment rendre ça simple sans perdre la puissance ? Piste : templates par plateforme (FastAPI, Express, etc.) + mode "just check if 200 + JSON".
- **Rabbit Hole #2 — Render Cron Job vs scheduler interne.** Render propose des Cron Jobs ($1/mo), mais ils sont limités (pas de state, cold start à chaque run). Un scheduler interne (APScheduler) tourne en continu mais consomme de la RAM. À trancher pendant le Walking Skeleton.
- **Rabbit Hole #3 — Dépendance externe email.** Si Resend/SendGrid est down, les alertes ne partent pas. Faut-il un fallback ? Probablement non pour le MVP — on documente le risque et on avance.
