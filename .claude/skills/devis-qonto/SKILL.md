---
name: devis-qonto
description: |
  Gestion conversationnelle des devis, factures, clients et articles Qonto via l'API Business.
  Utilise ce skill dès que la demande concerne un devis, une facture, un client ou un article côté Qonto :
  créer, modifier, lister, rechercher, valider un devis, envoyer par email, marquer payée, ou calculer
  les paiements en attente. N'utilise PAS ce skill pour les transactions bancaires (skill `qonto` séparé).
  Exemples : "devis 1500€ pour KSA prestation mars", "valide le devis DEV-042", "factures impayées de KSA",
  "combien de paiements en attente", "crée une facture pour ACME", "ajoute un article consulting 500€",
  "modifie l'email de KSA", "envoie le devis DEV-042 au client".
---

# Skill Devis-Qonto

Outil CLI Node.js dans `/Users/YarmaVideos/Developer/divers/Devis-Qonto/` qui expose l'API Business Qonto. Tu interagis avec Yannick en conversation, tu construis les payloads, et tu appelles le CLI. Tu présentes toujours un résumé avant tout POST et tu attends la validation explicite.

## Avant toute commande

Vérifie que `.env` existe dans le projet. Si `ping` retourne une erreur d'auth, dis à Yannick de vérifier `QONTO_ORGANIZATION_SLUG` / `QONTO_SECRET_KEY` dans `/Users/YarmaVideos/Developer/divers/Devis-Qonto/.env`.

## Defaults

| Champ | Valeur par défaut |
|---|---|
| `issue_date` | aujourd'hui (date système) |
| `expiry_date` (devis) | issue_date + 30 jours |
| `due_date` (facture) | issue_date + 30 jours |
| `currency` | `EUR` |
| `vat_rate` (par item) | `"0.085"` (DOM — format fraction décimale) |
| `number` | auto Qonto (ne pas envoyer de `number` manuel) |
| Statut facture initial | brouillon (`--finalize` uniquement sur confirmation) |

Les montants sont toujours en **string** : `"1500.00"`, pas `1500`.

## Commandes CLI disponibles

Toutes invoquées depuis `/Users/YarmaVideos/Developer/divers/Devis-Qonto/` :

```
node src/cli.js <command> [options]
```

**Base** : `ping`

**Clients** : `client-list`, `client-find "<nom>"`, `client-get --id`, `client-create --json <file>`, `client-update --id <id> --json <file>`

**Articles** : `product-list`, `product-find "<nom>"`, `product-get --id`, `product-create --json`, `product-update --id --json` (⚠️ delete+recreate = nouvel ID), `product-delete --id`

**Devis** : `quote-list [--client-id=] [--from=] [--to=]`, `quote-find "<terme>"`, `quote-get --id`, `quote-create --json`, `quote-update --id --json`, `quote-send --id --json`, `quote-validate --id`

**Factures** : `invoice-list [--status=] [--client-id=] [--from=] [--to=]`, `invoice-find "<terme>"`, `invoice-get --id`, `invoice-create --json [--finalize]`, `invoice-update --id --json`, `invoice-finalize --id`, `invoice-send --id --json`, `invoice-mark-paid --id [--paid-at=]`, `invoice-cancel --id`

**Rapports** : `pending-payments [--detailed]`

Les `--json` prennent le chemin vers un fichier JSON temporaire que tu crées dans `/tmp/devis-qonto-*.json`.

## Workflows

### 1. Créer un devis

**Déclencheurs** : "devis pour X", "nouveau devis", "crée un devis"

1. **Extrait** : client (nom), items (titre + quantité + éventuel prix HT + éventuelle description custom), remises (par item ou globale), dates
2. **Résous le client** :
   - Appelle `client-find "<nom>"`.
   - 1 match exact → utilise directement.
   - Plusieurs matchs → présente la liste numérotée, demande lequel.
   - 0 match → demande à Yannick : "client inconnu, on le crée ? Il me faut nom, email, adresse, SIRET." puis `client-create`.
3. **Résous chaque item via le catalogue articles** (règle importante) :
   - Pour chaque item demandé, appelle `product-find "<titre>"` pour trouver l'article catalogue.
   - **Si trouvé** : copie **textuellement** `title`, `description`, `unit_price`, `vat_rate` depuis le catalogue. Seule la `quantity` (et éventuellement une `discount`) viennent de la demande de Yannick.
   - **Si l'utilisateur a précisé une description spécifique** ("avec comme description X", "décris ça comme Y") : utilise la version custom.
   - **Si l'utilisateur a précisé un tarif différent** du catalogue : demande confirmation avant d'override ("le tarif catalogue est 800€/j, tu veux vraiment 900€ sur ce devis ?").
   - **Si 0 match catalogue** : demande à Yannick le titre, la description, le prix HT, la TVA.
4. **Construis le payload** (écris-le dans `/tmp/devis-qonto-quote-<ts>.json`) :
   ```json
   {
     "client_id": "<uuid>",
     "issue_date": "2026-04-16",
     "expiry_date": "2026-05-16",
     "currency": "EUR",
     "items": [
       {
         "title": "Tournage",
         "description": "Participation au tournage pour une OP d'influence du client",
         "quantity": "2",
         "unit_price": { "value": "800.00", "currency": "EUR" },
         "vat_rate": "0.085"
       }
     ]
   }
   ```
5. **Présente un résumé** à Yannick en indiquant la source de chaque description :
   ```
   DEVIS — <nom client>
   Émission : 16/04/2026 · Validité : 16/05/2026
   
   Item 1 : Tournage × 2j — 800.00€ HT (TVA 8.5%)
     Description (depuis catalogue) : "Participation au tournage pour une OP d'influence du client"
   
   Item 2 : Montage × 5j — 450.00€ HT (TVA 8.5%)
     Description (depuis catalogue) : "Suivi des étapes de post-production - Derush - Montage - Révision..."
   
   HT : 3850.00€
   TVA : 327.25€
   TTC : 4177.25€
   ```
   Indique clairement `(depuis catalogue)` ou `(description custom)` pour chaque item. Puis demande : "Je crée ? Ou tu veux ajuster une description ?"
6. **Sur validation** : `node src/cli.js quote-create --json <path>` → récupère `id`, `number`, `pdf_path`
7. **Ouvre le PDF dans Adobe Acrobat** : `open -a "Adobe Acrobat" <pdf_path>` (macOS). N'utilise PAS `open <path>` tout court — ça ouvre dans Aperçu par défaut.
9. **Propose l'envoi email** : "envoyer à `<email_client>` ? (copie à toi : oui)"
   - Si oui → crée `/tmp/devis-qonto-send-<ts>.json` avec `{ "send_to": ["<email>"], "email_title": "Devis <number>", "copy_to_self": true }` puis `quote-send --id <id> --json <path>`
   - L'email part depuis Qonto, pas depuis `contact@karata.fr`.

### 2. Créer une facture directement

Identique au devis, mais :
- Payload dans `client_invoices` : `due_date` au lieu de `expiry_date`
- `invoice-create` sans `--finalize` → crée un **brouillon** (pas de PDF, statut `draft`)
- Présente le brouillon → demande : "finaliser maintenant ? (une fois finalisée, la facture sera immuable)"
- Si oui → `invoice-finalize --id <id>` → PDF téléchargé
- Puis propose envoi email comme pour un devis

### 3. Valider un devis (devis accepté → facture)

**Déclencheurs** : "valide le devis X", "transforme le devis X en facture", "DEV-042 accepté"

1. **Résous le devis** :
   - Si numéro mentionné → `quote-find "<numéro>"`
   - Sinon "devis de KSA pour mars" → `quote-find "KSA mars"` ou combine recherche client + période
   - Si ambigu, présente la liste numérotée, demande lequel
2. **Présente le devis résolu** et demande confirmation : "valider `<number>` (<client>, <montant>€) ?"
3. **Sur validation** : `quote-validate --id <id>` → crée une facture **brouillon** à partir des items du devis et met à jour `state.json`
4. **Demande** : "finaliser la facture maintenant ? (immuable après finalisation)"
5. Si oui → `invoice-finalize --id <invoice_id>` → propose envoi email

### 4. Modifier un devis / une facture (brouillons uniquement)

**Déclencheurs** : "change le montant de X", "modifie le devis X", "remplace l'item Y sur X"

1. **Résous le doc** via `find` ou `get`
2. **Vérifie le statut** : seuls les brouillons sont modifiables. Si facture finalisée ou devis envoyé, **refuse** avec message clair : "le document <number> est <status>, impossible de le modifier — crée un avoir ou annule puis recrée".
3. **Construis le patch** (champs modifiés uniquement)
4. **Présente le patch** → Yannick valide
5. **Sur validation** : `quote-update` ou `invoice-update` avec le patch JSON

### 5. Appliquer une remise

- **Par item** : dans chaque item ajouter `"discount": { "type": "percentage", "value": "10" }` ou `"type": "amount", "value": "50.00"`
- **Globale** : au niveau racine du payload : `"discount": { "type": "percentage", "value": "5" }`
- **Cumulables** : un item peut avoir sa remise + le doc peut avoir une remise globale
- **Résumé explicite obligatoire** :
  ```
  HT brut : 2000.00€
  Remise item (5% sur Prestation A) : -25.00€
  Remise globale (10%) : -197.50€
  HT net : 1777.50€
  TVA 8.5% : 151.09€
  TTC : 1928.59€
  ```
- **Garde-fous** : le CLI refuse les % > 100 et les montants négatifs. Si Yannick demande une remise > 100%, dis-lui que c'est impossible.

### 6. Envoi email (devis ou facture)

- **Endpoints Qonto** : `quote-send` / `invoice-send`. L'email est envoyé **par Qonto** (pas par `contact@karata.fr`).
- Pas de CC/BCC, uniquement `send_to` (array) et `copy_to_self` (default `true` → Yannick reçoit une copie dans sa boîte mail Qonto).
- **Confirmation obligatoire** : montre destinataire + numéro + montant, demande "j'envoie ?".
- Body email : optionnel (Qonto met un template par défaut) — si Yannick dicte un message, mets-le dans `email_body`.

### 7. Lister les factures d'un client

**Déclencheurs** : "factures de X", "toutes les factures de X", "impayées de X"

1. `client-find "<nom>"` → récupère `client_id`
2. `invoice-list --client-id=<id>` (ajoute `--status=unpaid` si "impayées")
3. Formate en tableau :
   ```
   Factures de KSA (5) :
   
   FAC-2026-012 | 1500.00€ | unpaid  | émise 01/03/2026 | due 31/03/2026
   FAC-2026-008 | 2400.00€ | paid    | émise 15/02/2026
   ...
   
   Total impayé : 3500.00€
   ```

### 8. Somme des paiements en attente

**Déclencheurs** : "paiements en attente", "combien on nous doit", "créances"

1. `pending-payments --detailed`
2. Formate :
   ```
   PAIEMENTS EN ATTENTE — total 12 450.00€
   
   Par client :
   - KSA : 5 200.00€
   - ACME : 3 250.00€
   - ...
   
   Détail :
   Factures impayées (3) :
   - FAC-2026-012 | KSA | 1500€ | échue 31/03/2026
   - ...
   
   Devis validés non facturés payés (2) :
   - DEV-2026-042 | ACME | 2000€ | validé 10/03/2026
   - ...
   ```

### 9. CRUD clients

- **Créer** : `"nouveau client ACME, acme@test.fr, 12 rue X 75001 Paris, SIRET 12345678900001"` → construis payload → `client-create`
- **Modifier** : `"change l'email de KSA à nouveau@ksa.fr"` → `client-find` → `client-update --id --json {...}`
- **Lister** : `client-list`

### 10. CRUD articles

- **Créer** : `"article 'Consulting jour' à 500€ HT TVA 8.5%"` → `product-create`
- **Lister / Rechercher** : `product-list`, `product-find`
- **Modifier / Supprimer** : ⚠️ **Limitation Qonto** — les endpoints `DELETE /v2/products/{id}` et `GET /v2/products/{id}` retournent 404 sur ce compte (bug ou restriction Qonto, vérifié le 16/04/2026). Les commandes `product-update` et `product-delete` échoueront avec un message clair. Oriente Yannick vers l'interface web : <https://app.qonto.com> → Facturation → Articles. Une fois la modification faite côté web, `product-list` reflétera le nouvel état.

**Important — descriptions catalogue vs devis** :
- Modifier la **description d'un article catalogue** (ex. "change la description du Tournage pour X") → via interface web Qonto uniquement (voir ci-dessus).
- Modifier la **description d'un item sur un devis spécifique** (ex. "sur le devis DEV-042, remplace la description du Tournage par X") → via `quote-update --id --json` (brouillon uniquement). Cela ne touche pas l'article catalogue, juste ce devis.

## Règles de sécurité (guardrails)

1. **Jamais de POST sans résumé + validation explicite** de Yannick.
2. **Jamais d'envoi email automatique** : confirmation obligatoire (destinataire + montant visibles).
3. **Finalisation de facture = immuable** : confirmation explicite avec message "une fois finalisée, la facture ne pourra plus être modifiée".
4. **Modification de doc finalisé = refus** avec message clair (pas de tentative de workaround).
5. **Produit update/delete via API = 404 sur ce compte Qonto** → oriente vers l'interface web.
6. **Pas de `quote-delete` / `invoice-delete` / `client-delete`** exposés dans le CLI. Si Yannick demande, oriente vers l'interface web Qonto.
7. **Dates relatives** ("mars", "semaine prochaine") : résous en ISO (`YYYY-MM-DD`) avant l'appel CLI. Date courante = 2026-04-16.
8. **Montants** toujours en string (`"1500.00"`), **TVA en fraction décimale** (`"0.085"` pour 8.5%, `"0.2"` pour 20%, `"0"` pour exonéré), remises en string (`"10"`).

## Gestion des erreurs

| Erreur | Action |
|---|---|
| `401 Unauthorized` | Dis à Yannick : "credentials invalides — vérifie `.env` et les scopes API (`client_invoice.write`, `client.write`, `product.write`, reads associés, `organization.read`)" |
| `422 Validation error` | Parse les champs en erreur, remonte précisément ce qui manque/est invalide |
| `429 Rate limit` | Le CLI retry une fois automatiquement. Si ça persiste, attends et réessaie |
| `Quote/Invoice is <status>, only drafts can be modified` | Explique à Yannick que le doc est déjà envoyé/finalisé, il faut annuler ou créer un avoir |

## Chemins clés

- Projet : `/Users/YarmaVideos/Developer/divers/Devis-Qonto/`
- CLI : `node src/cli.js <command>` (depuis le dossier projet)
- PDF sauvegardés : `pdf/` (nom original Qonto)
- Exemples JSON : `examples/`
- État local : `state.json` (mapping `quote_id ↔ invoice_id` pour les devis validés)
