# Build Walkthrough — Scope 1 : Les Smoke Tests Fonctionnels

## Ce qu'on a fait

On est passe de "le serveur repond" a "la feature marche vraiment." C'est la difference fondamentale entre un health check et un smoke test.

Un health check, c'est comme appeler un restaurant : "Allo, vous etes ouverts ?" — "Oui." Ca ne te dit pas si la cuisine fonctionne, si le chef est la, ou si tu vas pouvoir manger.

Un smoke test, c'est comme commander un plat : tu envoies une vraie commande et tu verifies que tu recois quelque chose de comestible. Si le serveur repond "on n'a plus de gaz", tu sais que le restaurant est ouvert mais que la cuisine est cassee.

## Pourquoi c'est non-negociable

On a decouvert ca pendant le build : **plusieurs projets passaient le health check mais etaient en realite casses.**

- **DataPilot** avait "Deployed" sur Render mais une mauvaise URL configuree. Le health check passait (Render repond 200 sur la racine), mais aucune feature ne marchait.
- **WatchNext** passait le health check mais avait un RateLimitError d'OpenAI. Le serveur tournait, mais les recommandations ne fonctionnaient plus.

Sans smoke test, on aurait cru que tout allait bien. En demo, ca aurait plante devant le recruteur.

## Comment ca marche

```
Configuration par projet :
  - smoke_endpoint : "/classify" (quel endpoint tester)
  - smoke_method : "POST" (quelle methode HTTP)
  - smoke_payload : {"dataset": "demo"} (quoi envoyer)
  - smoke_payload_type : "form" ou "json" (quel format)
  - smoke_validate_field : "success" (quel champ verifier dans la reponse)

Execution :
  1. Envoyer la requete configuree
  2. Verifier que la reponse est HTTP 200
  3. Verifier que la reponse contient le champ attendu
  4. Si tout passe : PASS + latence
  5. Si echec : FAIL + message d'erreur precis
```

Chaque projet a sa propre configuration de smoke test adaptee a ce qu'il fait :

| Projet | Endpoint | Payload | Validation |
|--------|----------|---------|------------|
| DocuQuery | `/query` | `{"question": "What is..."}` | Champ `answer` present |
| WatchNext | `/recommend` | `{"mood": "fun"}` | Champ `movies` present |
| DataPilot | `/analyze` | `{"question": "Show..."}` | Champ `success` present |
| FeedbackSort | `/classify` | `{"dataset": "demo"}` | Champ `success` present |
| EvalKit | `/demo` | (aucun) | Champ `success` present |

## Le detail technique qui compte : JSON vs form data

Tous les projets n'envoient pas leurs donnees de la meme facon. DocuQuery et WatchNext utilisent du JSON (un format structure). FeedbackSort et DataPilot utilisent des formulaires (form data) — comme quand tu remplis un formulaire sur un site web.

Le moteur de check devait supporter les deux. C'est un detail invisible pour l'utilisateur mais crucial : si tu envoies du JSON a un endpoint qui attend un formulaire, ca plante avec une erreur incomprehensible.

## Le bug CORS

CORS (Cross-Origin Resource Sharing) est un mecanisme de securite des navigateurs. Quand le frontend (heberge sur Lovable) essaie de parler au backend (heberge sur Render), le navigateur bloque la requete par defaut — c'est comme un vigile qui refuse l'entree parce que le visiteur n'est pas sur la liste.

Le fix : dire au backend "accepte les requetes de Lovable." Deux lignes de code, 30 minutes de debug. C'est un classique des projets frontend + backend separes — on l'a rencontre sur chaque projet du portfolio.

## La lecon

Le health check est necessaire mais pas suffisant. C'est la couche 1. Le smoke test est la couche 2 — celle qui te dit si ton produit marche *pour de vrai*. ShipWatcher sans smoke test, c'est un mensonge rassurant. Avec le smoke test, c'est la verite, meme quand elle fait mal.
