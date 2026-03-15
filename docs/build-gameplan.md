# BUILD Gameplan

> Template from The Builder PM Method — BUILD phase (start)

---

**Project Name:** ShipWatcher
**Date:** 2026-03-14
**Cycle Appetite:** 1 semaine (side project)
**MVP Features (from 1-Pager):**
- Smoke test fonctionnel (vraie requête + validation réponse)
- Dashboard web (statut live de tous les projets)
- Alertes email automatiques
- Mode pre-demo (warmup + check all now)
- Config via formulaire web (ajouter/modifier un projet)

**Riskiest Assumption (from 1-Pager):**
"Un builder solo va configurer ses endpoints de test (pas juste un ping) ET consulter les résultats assez régulièrement pour que le monitoring ait de la valeur — le tout en moins de 2 minutes de setup."

---

## Context Setup

**Action :** Le 1-Pager est dans `docs/1-pager.md`. Le CLAUDE.md du projet sera créé au début du Walking Skeleton. Le frontend sera construit sur Lovable avec le 1-Pager comme contexte initial.

---

## Walking Skeleton

> La tranche la plus fine qui va de bout en bout et teste la Riskiest Assumption.

**What it does :** Un utilisateur arrive sur le dashboard, ajoute un projet (URL + endpoint de test), clique "Check Now", et voit le résultat (vert/rouge) avec la latence.

**End-to-end path :** Formulaire web (URL + endpoint) → Backend reçoit la config → Backend envoie une requête HTTP au projet cible → Backend valide la réponse → Dashboard affiche le résultat (PASS/FAIL + latence)

**Done when :** Un utilisateur peut ajouter un projet et voir son statut en < 2 min de setup.

**Micro-tests :**

| # | Test | Input | Expected | Pass Criteria |
|---|------|-------|----------|---------------|
| WS-1 | Ajouter un projet avec URL valide | URL: `https://docuquery-ai-5rfb.onrender.com`, Health endpoint: `/health` | Projet ajouté, visible dans la liste | Le projet apparaît dans le dashboard avec son nom et URL |
| WS-2 | Check Now sur un projet UP | Cliquer "Check Now" sur DocuQuery AI | Statut vert, latence affichée (ex: 300ms) | Statut = PASS, latence > 0ms, affiché en < 5s |
| WS-3 | Check Now sur un projet DOWN | URL: `https://fake-project-doesnotexist.onrender.com`, endpoint `/health` | Statut rouge, message d'erreur | Statut = FAIL, erreur affichée (timeout ou connection error) |
| WS-4 | Adversarial — URL invalide | URL: `not-a-url` | Erreur de validation côté formulaire | Le formulaire rejette l'URL avant d'envoyer au backend |
| WS-5 | Setup time | Chronomètre : ouvrir le dashboard → ajouter un projet → voir le résultat | < 2 minutes | Le flow complet prend moins de 2 min |

→ **Gate : 5/5 PASS → Skeleton Check.** La Riskiest Assumption tient si WS-5 < 2 min ET WS-2 montre un résultat fiable.

---

## Scope 1 : Smoke Tests Fonctionnels

**What it adds :** Au-delà du simple health check, l'utilisateur peut configurer un vrai test fonctionnel — un endpoint, un payload JSON, et une règle de validation de la réponse. Le dashboard affiche "Health OK" vs "Feature OK".

**Done when :** Un utilisateur peut configurer un smoke test sur un projet et voir si la feature marche vraiment (pas juste le serveur).

**Micro-tests :**

| # | Test | Input | Expected | Pass Criteria |
|---|------|-------|----------|---------------|
| S1-1 | Configurer un smoke test avec payload JSON | Projet WatchNext, endpoint `/recommend`, payload `{"mood": "fun comedy"}`, validation: `movies in response` | Config sauvegardée, visible dans le détail du projet | Le smoke test apparaît dans la config du projet |
| S1-2 | Run smoke test sur un projet fonctionnel | Exécuter le smoke test WatchNext | Statut vert, latence affichée, "Feature OK" | Réponse validée, `movies` présent dans la réponse, latence affichée |
| S1-3 | Run smoke test qui fail (feature cassée) | Endpoint `/recommend`, payload `{"mood": "test"}`, validation: `nonexistent_field in response` | Statut rouge, "Feature FAIL", détail de l'erreur | Le dashboard distingue clairement "serveur UP mais feature cassée" |
| S1-4 | Health check + smoke test ensemble | Run les deux checks sur le même projet | Deux résultats distincts affichés | Dashboard montre 2 lignes : "Health: PASS" et "Smoke: PASS/FAIL" |
| S1-5 | Config smoke test avec form data (pas JSON) | Projet FeedbackSort, endpoint `/classify`, form data `dataset=demo` | Config sauvegardée avec type "form" | Le système supporte les deux formats (JSON et form data) |

→ **Gate : 5/5 PASS**

---

## Scope 2 : Alertes Email + Scheduling

**What it adds :** Les checks tournent automatiquement (toutes les 6h). Quand un check fail, l'utilisateur reçoit un email. Plus besoin de venir sur le dashboard manuellement.

**Done when :** L'utilisateur configure son email, les checks tournent en cron, et il reçoit un email quand un projet tombe.

**Micro-tests :**

| # | Test | Input | Expected | Pass Criteria |
|---|------|-------|----------|---------------|
| S2-1 | Configurer l'email d'alerte | Entrer `mehdi@example.com` dans les settings | Email sauvegardé | L'email est stocké et affiché dans les settings |
| S2-2 | Recevoir un email quand un check fail | Ajouter un projet avec une URL morte + attendre le cron (ou trigger manuel) | Email reçu avec : nom du projet, type d'erreur, timestamp | Email reçu dans la boîte, contenu lisible et actionable |
| S2-3 | PAS d'email quand tout va bien | Tous les projets sont UP, le cron tourne | Aucun email | Zéro email envoyé (pas de spam "tout va bien") |
| S2-4 | Cron tourne automatiquement | Configurer un intervalle de 1 min (pour le test), attendre 2 min | Au moins 2 runs visibles dans le log | Le scheduler exécute les checks à l'intervalle prévu |
| S2-5 | Pre-demo mode | Bouton "Check All Now" qui lance tous les checks immédiatement | Tous les résultats rafraîchis, warmup effectué | Résultats frais affichés pour TOUS les projets en < 60s |

→ **Gate : 5/5 PASS**

---

## Scope 3 : Dashboard Polish + Deploy

**What it adds :** Le dashboard devient visuellement clair (couleurs, icônes, dernière vérification), le projet est déployé sur Render, l'URL est publique et partageable.

**Done when :** Un inconnu peut aller sur l'URL, comprendre ce que fait ShipWatcher, et ajouter son premier projet.

**Micro-tests :**

| # | Test | Input | Expected | Pass Criteria |
|---|------|-------|----------|---------------|
| S3-1 | Compréhension en 10s | Montrer le dashboard à quelqu'un (ou juger soi-même) | La personne comprend "c'est un monitoring pour mes projets" | Titre + description + CTA clairs, pas de jargon |
| S3-2 | Statut visuel immédiat | 5 projets avec mix UP/DOWN | Vert = UP, Rouge = DOWN, dernière vérification affichée | Les couleurs sont distinctes, le "last checked" est visible |
| S3-3 | Supprimer un projet | Cliquer supprimer sur un projet | Projet retiré de la liste | Le projet disparaît, les checks s'arrêtent |
| S3-4 | Déploiement Render | Accéder à l'URL publique depuis un autre appareil | Le dashboard charge et fonctionne | Page chargée en < 3s, tous les checks fonctionnent |
| S3-5 | Mobile responsive | Ouvrir le dashboard sur mobile | Layout lisible, pas de scroll horizontal | Tous les éléments sont visibles et utilisables |
| S3-6 | Modifier un projet existant | Changer l'URL d'un projet | Nouvelle URL prise en compte au prochain check | Le check suivant utilise la nouvelle URL |

→ **Gate : 6/6 PASS**

---

## Compliance Tracker (DOR/DOD)

| Slice | R1 | R2 | R3 | R4 | R5 | D1 | D2 | D3 | D4 | D5 |
|-------|----|----|----|----|----|----|----|----|----|----|
| WS | — | | | ✓ | | | | | | |
| Scope 1 | | | | ✓ | | | | | | |
| Scope 2 | | | | ✓ | | | | | | |
| Scope 3 | | | | ✓ | | | | | | |

R4 (micro-tests définis AVANT de coder) est déjà rempli pour toutes les slices ci-dessus.

---

## Exit Criteria (BUILD → EVALUATE)

- [ ] Toutes les features MVP du 1-Pager fonctionnelles end-to-end
- [ ] Riskiest Assumption testée (Skeleton Check passé — setup < 2 min)
- [ ] Open Questions du 1-Pager résolues ou converties en ADRs
- [ ] Build Log à jour
- [ ] Prêt pour évaluation formelle contre les Success Metrics
