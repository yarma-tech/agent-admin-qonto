# Guide d'entretien — Validation Decidia

**Objectif** : valider (ou invalider) la promesse racine de Decidia — *"envoyer un devis en 2 minutes au lieu de 24-48h transforme la vie d'un freelance créatif"* — auprès de 5 à 10 vidéastes/motion designers solo en France, **avant** d'investir dans le développement des apps natives.

**Critère de succès du sprint validation** : à l'issue des 5-10 entretiens, on doit pouvoir trancher sans ambiguïté entre :
- ✅ **GO** : le pain point est réel, la promesse rezone, le prix 99-249€ est jugé "no-brainer"
- ❌ **NO-GO** : le pain est exagéré dans nos hypothèses, OU les freelances ont déjà adapté leur workflow, OU le prix est jugé trop cher pour le bénéfice perçu
- 🔄 **PIVOT** : le pain est réel mais sur un angle différent (ex : c'est la relance paiement qui les tue, pas la rédaction du devis)

---

## 1. Profil cible des interviewés

**Indispensable** :
- Vidéaste / motion designer / réalisateur **freelance solo** (pas en agence ni avec assistant)
- En activité depuis au moins **12 mois** (a vécu plusieurs cycles devis-facture)
- Fait au moins **3 devis par mois** en moyenne (sinon le pain n'est pas suffisamment fréquent)
- Compte pro **Qonto OU Shine OU Pennylane** (notre cœur de cible technique)
- Basé en **France** (langue, contexte fiscal, communautés)

**À éviter** :
- Vidéastes salariés ou en agence avec un comptable (ils n'ont pas le pain)
- Très jeunes freelances (<6 mois d'activité, biais débutant)
- Très gros freelances (>100k€/an, ils ont externalisé)

**Mix idéal sur 8 entretiens** :
- 4 vidéastes corpo / mariage / événementiel (gros volume devis)
- 2 motion designers (ticket plus petit, fréquence haute)
- 2 réalisateurs/DA pub (ticket plus gros, fréquence faible) — pour tester l'autre extrême

---

## 2. Comment recruter

**Sources prioritaires** (gratuites, qualifiées) :
- **Réseau perso** : LinkedIn / Insta / contacts directs — **commencer par là**, c'est le plus rapide
- **Discord motion design FR** : poser un message dans #freelance ou #cafe → "Je recherche 8 vidéastes/motion freelance pour 30 min de discussion sur leurs galères admin. Pas de pitch produit, juste comprendre. Visio ou tel. En échange : un café offert (carte cadeau 10€)"
- **Facebook Vidéastes Indé** (groupe ~15k membres FR)
- **Reddit r/VideoEditing_FR**
- **Twitter/X** : poster un appel avec hashtag #freelance #vidéaste

**Incentive** : carte cadeau 10€ (Amazon, Starbucks, FNAC) pour chaque entretien complété. Symbolique mais montre que tu respectes leur temps. Budget total : 80-100€.

**Délai réaliste** : 1 semaine pour caler les 8 entretiens, 1 semaine pour les faire, 2-3 jours pour synthétiser. **Sprint total : 2 à 3 semaines.**

---

## 3. Préparation entretien

**Format** : 30-45 min, visio (Google Meet, Zoom) ou téléphone. Préfère visio (langage corporel = signal).

**Outils** :
- **Enregistrement** : OBLIGATOIRE (avec consentement explicite au début). Permet de réécouter et noter à froid. Otter.ai ou Whisper local pour transcription auto.
- **Calendly** ou similaire pour le booking sans friction
- **Document de notes** : un par entretien, dans `docs/validation/notes/2026-04-XX-prenom.md` (template plus bas)

**État d'esprit** :
- **Tu n'as PAS de produit à vendre.** Si tu pitches, tu biaises tout et tu n'apprends rien.
- **Tu écoutes 80% du temps**, tu parles 20%.
- **Ton ennemi #1 = les questions hypothétiques** ("si on te proposait X, tu paierais ?"). Réponses = 90% mensonges polis. Remplace par des questions sur le comportement passé concret.
- **Cherche les émotions** : irritation, soulagement, fierté, honte. C'est là que se cache la vraie valeur.
- **Lis "The Mom Test"** de Rob Fitzpatrick si pas déjà fait — 90 pages, le manuel parfait pour ces entretiens.

---

## 4. Structure d'entretien (40 min)

### Introduction (3 min)
- Présente-toi simplement : *"Je m'appelle [prénom], je suis vidéaste freelance comme toi. Je travaille sur un projet qui touche à la galère des devis pour les freelances créatifs. Avant de coder quoi que ce soit, je veux comprendre comment vous fonctionnez vraiment. Cet entretien, c'est pas un pitch — c'est moi qui apprend de toi."*
- Demande l'autorisation d'enregistrer.
- Rassure : *"Je vais te poser des questions sur ton quotidien, parfois bêtes ou évidentes. Réponds spontanément, il n'y a pas de mauvaise réponse. Si une question te met mal à l'aise, tu peux passer."*

### Découverte du métier (8 min)
**Objectif** : comprendre son contexte, créer du rapport, débloquer la parole.

- *"Raconte-moi ton activité — qu'est-ce que tu fais comme vidéos ?"*
- *"Depuis combien de temps t'es freelance ? Comment t'as commencé ?"*
- *"À peu près combien de clients différents tu sers par mois ?"*
- *"Quels sont les pires et les meilleurs aspects de ton métier ? Quand tu te lèves le matin, qu'est-ce qui te donne envie / pas envie ?"*

### Workflow devis actuel (15 min — LA SECTION CLÉ)
**Objectif** : reconstituer dans le détail le dernier devis, identifier les vraies frictions.

⚠️ **Pose des questions sur des comportements PASSÉS, pas hypothétiques.**

- *"Raconte-moi ton dernier devis. Quel client, quelle prestation ?"*
- *"À quel moment tu as appris que tu devais faire ce devis ? Comment le client te l'a demandé ?"* (téléphone, mail, brief, recommandation…)
- *"Combien de temps s'est écoulé entre 'le client te demande' et 'tu as envoyé le PDF' ? Sois précis : heures, jours."*
- *"Pendant ce temps, qu'est-ce qui s'est passé exactement ? Tu l'as fait quand ? Le soir ? Le week-end ? Entre deux missions ?"*
- *"À quel moment tu as commencé à le rédiger concrètement ? Pourquoi pas avant ?"* (chercher la procrastination, les blocages)
- *"Quelles sont les étapes de la rédaction ? Tu utilises quel outil ?"*
- *"Y a-t-il eu des allers-retours avec le client ?"*
- *"Quand tu as envoyé, combien de temps avant le client a répondu ? A-t-il signé ?"*

**Variantes pour creuser** :
- *"Sur tes 3 derniers devis, lequel a été le plus pénible à faire ? Pourquoi ?"*
- *"As-tu déjà perdu un client parce que tu n'as pas répondu assez vite ? Raconte."*
- *"As-tu déjà signé un client parce que tu as répondu plus vite qu'un concurrent ? Raconte."*

### Douleurs et émotions (8 min)
**Objectif** : faire émerger les vraies frustrations émotionnelles.

- *"Quand tu dois faire un devis, qu'est-ce que tu ressens ? Énervement ? Indifférence ? Stress ?"*
- *"Y a-t-il des soirs ou des week-ends où tu te dis 'merde, faut que je fasse mes devis' ?"* (cherche la procrastination émotionnelle)
- *"Si tu pouvais magiquement déléguer une seule tâche admin à quelqu'un, ce serait laquelle ? Pourquoi celle-là ?"*
- *"Combien de temps par mois tu passes sur tes devis et factures, à la louche ?"*
- *"Si t'avais 5h de plus par mois, tu en ferais quoi ?"* (chiffrer la valeur du temps gagné)

### Solutions actuelles (3 min)
**Objectif** : comprendre ce qu'il a déjà essayé, ce qui marche / ne marche pas.

- *"Tu utilises quoi pour faire tes devis aujourd'hui ?"* (Qonto natif, Pennylane, Word, Excel, Indy…)
- *"T'as déjà essayé d'autres outils ? Pourquoi tu les as abandonnés ?"*
- *"As-tu déjà entendu parler d'outils IA pour la facturation ?"* (test connaissance concurrents)
- *"Combien tu paies aujourd'hui en outils admin par mois (compta, facturation) ?"*

### Réaction au concept (3 min — UNIQUEMENT À LA FIN)
**Objectif** : observer la réaction sincère, sans biaiser tout l'entretien.

Présente le concept **en 30 secondes max, sans pitch commercial** :
> *"Pour info — je travaille sur un truc qui s'appelle Decidia. L'idée : tu sors d'un tournage, tu prends ton iPhone, tu dis à voix haute 'devis pour Marc, 2 jours de tournage à 800€/jour, livraison J+10', et 90 secondes plus tard le PDF est envoyé au client. Tout ça connecté à ton Qonto. Qu'est-ce que t'en penses ?"*

**Écoute attentivement** :
- Première réaction émotionnelle (intérêt, scepticisme, indifférence) — c'est le signal le plus pur
- Premières objections ("ouais mais…") — c'est ce qu'il faudra adresser dans le marketing
- A-t-il des suggestions spontanées ? (signe d'engagement)

**Ne JAMAIS demander** :
- ~~"Tu paierais combien ?"~~ → réponses = mensonges
- ~~"Tu l'utiliserais ?"~~ → tout le monde dit oui pour faire plaisir

**Demander à la place** :
- *"Sur une échelle de 1 à 10, à quel point ce truc te parle ?"*
- *"Si je sors ça dans 3 mois, j'ai ton mail pour te prévenir ?"* (test engagement réel)
- *"Tu connais d'autres vidéastes à qui je devrais parler ?"* (test recommandation = vrai indicateur de valeur perçue)

### Clôture (1 min)
- *"Merci, c'était super utile. Je t'envoie ta carte cadeau aujourd'hui."*
- *"Je te tiens au courant si je sors un truc. Bonne continuation."*

---

## 5. Template de notes par entretien

Crée un fichier `docs/validation/notes/2026-04-XX-prenom.md` avec :

```markdown
# Entretien — [Prénom Nom]

**Date** : YYYY-MM-DD
**Durée** : XX min
**Source** : [comment recruté]

## Profil
- Métier : 
- Ancienneté freelance : 
- Volume devis/mois : 
- Outil banque : 
- Outil compta : 

## Workflow devis (le dernier)
- Délai demande → envoi : 
- Outil utilisé : 
- Frictions identifiées : 
- Histoire de "perdu un client à cause de la lenteur" : 

## Émotions
- Ce qui l'énerve le plus : 
- Temps consacré aux devis/mois : 
- Ce qu'il ferait avec le temps gagné : 

## Solutions actuelles
- Stack actuel : 
- Coût mensuel admin : 
- Ce qu'il a essayé puis abandonné : 

## Réaction au concept Decidia
- Note 1-10 : 
- Première phrase : 
- Objections : 
- A donné son mail ? : oui/non
- A recommandé d'autres personnes ? : combien

## Citations marquantes
> "..."

## Mes hypothèses confirmées / infirmées / nuancées
- 
- 
```

---

## 6. Synthèse après les 8 entretiens

Crée un fichier `docs/validation/synthese-2026-04.md` avec :

### Métriques quantitatives
- Délai moyen demande→envoi (sur les 8) : ___ heures
- % qui ont déjà perdu un client à cause de la lenteur : __%
- % qui ont signé un client grâce à la rapidité : __%
- Temps moyen consacré aux devis/mois : ___ heures
- Note moyenne d'intérêt (1-10) : __/10
- % qui ont donné leur mail pour la suite : __%
- Nb de recommandations spontanées de pairs : ___

### Patterns qualitatifs
- Top 3 douleurs récurrentes
- Top 3 objections récurrentes
- Citations les plus parlantes (3-5)

### Décision GO / NO-GO / PIVOT

**GO si** :
- Délai moyen ≥ 12h (confirme le pain "lenteur")
- Note moyenne d'intérêt ≥ 7/10
- ≥ 60% donnent leur mail
- ≥ 30% recommandent un pair (signal de valeur perçue forte)

**NO-GO si** :
- Note moyenne ≤ 5/10
- ≤ 20% donnent leur mail
- Pattern récurrent : "j'ai déjà résolu ça avec [outil X]"

**PIVOT si** :
- Le pain est réel mais ailleurs (relance paiement, déclaration TVA, etc.)
- L'idée intéresse mais l'angle "voix" rebute (préférence chat texte)
- Le profil cible est mal défini (les motion designers sont chauds, les vidéastes corpo non)

---

## 7. Risques de biais à éviter

- **Biais du pitch** : si tu commences par décrire Decidia, tu obtiens des "oui c'est génial" qui ne valent rien. Garde le concept pour la fin.
- **Biais de l'ami sympa** : ton réseau te dit oui pour te faire plaisir. Pondère leurs réponses.
- **Biais de la demande déclarée vs comportement réel** : "oui je paierais 99€" ≠ "j'ai sorti ma CB". Le seul vrai test = engagement (mail, recommandation).
- **Biais de confirmation** : tu vas chercher ce qui valide ton idée. Tiens un journal des signaux **contraires** à ton hypothèse.

---

## 8. Après le sprint

Si **GO** : on passe à la Phase 2.5 (Foundation HTTP) avec un plan dérisqué.
Si **NO-GO** : on archive Decidia, on fait debrief des apprentissages, on cherche un autre angle.
Si **PIVOT** : on reformule la promesse et on refait un sprint validation court (3-5 entretiens) sur le nouvel angle.

Le coût de ce sprint (2-3 semaines de ton temps + 80-100€ d'incentives) est **dérisoire** par rapport au coût d'une Phase 2.5 + Phase 3 (3-6 mois) lancée sur des hypothèses fausses.
