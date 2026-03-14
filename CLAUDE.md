# ShipWatcher

## Contexte
Monitoring automatique pour builders qui shippent des side projects. L'utilisateur ajoute ses projets (URL + endpoint), ShipWatcher vérifie qu'ils marchent vraiment (pas juste un ping) et alerte par email si quelque chose casse.

## Phase actuelle
**BUILD — Scope 3 (Dashboard Polish + Deploy)**

## Architecture
- **Backend :** FastAPI (Python) — hébergé sur Render
- **Frontend :** React + Tailwind (Lovable)
- **Stockage :** JSON file (MVP) — pas besoin de DB pour 10-50 projets
- **Checks :** httpx async — health check + smoke test fonctionnel
- **Alertes :** Email via Resend (à venir Scope 2)

## Fichiers clés
- `docs/1-pager.md` — FRAME complet
- `docs/build-gameplan.md` — Gameplan avec micro-tests
- `api.py` — Backend FastAPI
- `checker.py` — Moteur de checks (health + smoke)
- `store.py` — Stockage projets (JSON file)
- `monitor.py` — Prototype CLI (référence, pas le produit final)

## Conventions
- Python : snake_case
- Fichiers : kebab-case
- Pas de jargon dans les réponses API côté user

## Build Rules actives
- Micro-test = gate (pas d'étape)
- Vertical slices uniquement
- PM Validation Gate (zero commit sans GO)
