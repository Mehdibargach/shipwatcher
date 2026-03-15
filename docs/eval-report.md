# Eval Report — ShipWatcher

**Project:** ShipWatcher
**Date:** 2026-03-14
**Evaluator:** Claude + Mehdi
**Build Version:** `a87b73b`
**Test Suite:** 11 tests (détection, email, sécurité, performance)

---

## Eval Gate Decision

**GO** — Tous les critères BLOCKING passent. Le produit détecte correctement les pannes, envoie les alertes, et rejette les inputs malveillants.

### Criteria Levels

| # | Critère | Level | Seuil | Résultat | Status |
|---|---------|-------|-------|----------|--------|
| G1 | Détection UP correcte | BLOCKING | 100% | 100% (3/3 runs) | **PASS** |
| G2 | Détection DOWN correcte | BLOCKING | 100% | 100% (fake project → FAIL détecté) | **PASS** |
| G3 | Smoke test distingue health vs feature | BLOCKING | Détecte feature cassée quand serveur UP | health=UP, smoke=UP (ou smoke=FAIL quand OpenAI down) ✅ | **PASS** |
| G4 | Alerte email livrée | BLOCKING | Email reçu dans la boîte | Reçu à me.bargach@gmail.com ✅ | **PASS** |
| G5 | Daily digest livré | QUALITY | Email reçu avec tableau complet | Reçu avec 9/9 checks, format correct ✅ | **PASS** |
| G6 | Zéro faux positif | BLOCKING | 0 faux positif sur 3 runs consécutifs | 0/3 faux positifs ✅ | **PASS** |
| G7 | Sécurité — URL validation | BLOCKING | XSS et URL vides rejetés | `javascript:alert(1)` rejeté, URL vide rejetée ✅ | **PASS** |
| G8 | Seed data survit au redeploy | QUALITY | 6 projets présents après redeploy | 6/6 chargés depuis seed.json ✅ | **PASS** |
| G9 | Setup time | QUALITY | < 2 min | < 1 min ✅ | **PASS** |
| G10 | Check All latence | SIGNAL | < 120s | 64.9s ✅ | **PASS** |
| G11 | Pas de spam (pas d'email quand tout va bien) | QUALITY | 0 email inutile | Logs : "All checks passed — no alert needed" ✅ | **PASS** |

### Résumé

- **BLOCKING :** 5/5 PASS
- **QUALITY :** 4/4 PASS
- **SIGNAL :** 1/1 PASS

**Decision : GO → SHIP**

---

## Regression Check

| # | Feature | Test | Résultat | Status |
|---|---------|------|----------|--------|
| R1 | CRUD projets | Ajouter + supprimer un projet | Fonctionne ✅ | PASS |
| R2 | Health checks | Check sur 6 projets | 6/6 UP ✅ | PASS |
| R3 | Smoke tests | Check WatchNext /recommend | Réponse validée, `movies` présent ✅ | PASS |
| R4 | Check All | 11 checks exécutés | 11/11 PASS ✅ | PASS |

---

## Failure Analysis

Aucun échec détecté pendant l'évaluation. Observations :

| Observation | Type | Impact | Action |
|-------------|------|--------|--------|
| Check All prend 65s (FeedbackSort = 45s à lui seul) | SIGNAL | UX — l'utilisateur attend longtemps | V2 : exécuter les checks en parallèle, pas séquentiellement |
| Email arrive en spam (première fois) | SIGNAL | L'utilisateur rate l'alerte | V2 : domaine vérifié sur Resend ou instruction "marquer comme non-spam" |
| Stockage JSON éphémère sur Render | Résolu | Les projets ajoutés via dashboard sont perdus au redeploy | Résolu avec seed.json. V2 : SQLite sur disque persistant |

---

## Recommendations (GO)

Le produit est prêt à SHIP. Observations pour V2 :
1. **Checks en parallèle** — réduirait la latence de Check All de 65s à ~15s
2. **Domaine email vérifié** — éviter les spams
3. **Historique des checks** — timeline pour voir les tendances
4. **SQLite** — stockage persistant des projets ajoutés via dashboard
