---
name: correction-transcription
description: "Corriger les transcriptions de réunion (noms propres, acronymes, speakers) et générer un compte-rendu structuré. Utiliser quand l'utilisateur demande de corriger un transcript, nettoyer une transcription automatique, ou traiter une note de réunion avec diarisation (SPEAKER_00, SPEAKER_01, etc.)."
---

# Correction de transcription & compte-rendu

## Objectif

Corriger les erreurs de transcription dans les notes de réunion et produire un compte-rendu structuré.

## Workflow

1. Lire la note à corriger
2. **Récupérer le contexte des notes collaboratives liées** (voir section ci-dessous, optionnel) — étape utile pour disposer des notes prises en réunion en plus du transcript brut
3. Identifier les speakers : utiliser les indications du prompt (ex. "SPEAKER_00 = Alice") ou déduire des indices contextuels (qui se présente, qui est interpellé par son prénom, les sujets nommés dans les notes collaboratives, etc.)
4. **Checkpoint d'incertitude (obligatoire — voir section ci-dessous)** : avant toute écriture de correction, lister tous les éléments dont la confiance est <90 % et attendre confirmation utilisateur. Bloquer les étapes suivantes tant que la passe n'a pas été validée.
5. Remplacer les `SPEAKER_XX` par les vrais prénoms/noms dans tout le transcript
6. Corriger les erreurs (noms mal orthographiés, acronymes incorrects) en utilisant les référentiels personnels (voir section ci-dessous) **et les noms propres/acronymes présents dans les notes collaboratives**
7. Ajouter le titre `## Transcript de la réunion` au-dessus du transcript corrigé
8. Générer un `## Compte-rendu de la réunion` en début de note, en croisant transcript corrigé **et notes collaboratives** (les notes collaboratives reflètent les décisions/actions formalisées)
9. Écrire le résultat final **dans la note locale uniquement** — ne pas republier vers la source des notes collaboratives. **Wikifier les entités citées dans le compte-rendu uniquement** (pas dans le transcript brut) : pour chaque personne / organisation / produit / concept ayant une fiche dans `Entities/` (ou `Entités/`), entourer la 1ère occurrence par `[[Nom]]`. Pas de re-wikification à toutes les mentions (cf. règle Karpathy "1× par nom par fichier").
10. **Proposer un renommage si nécessaire** : une fois les speakers identifiés et confirmés, vérifier que le nom de fichier suit la convention `[Participant 1] x [Participant 2] x [...] - JJ.MM.AAAA.md` (cf. section ci-dessous). Si la note est dans `<meeting-notes>/À router/`, dans `<meeting-notes>/Ad-hoc/`, ou si le nom actuel ne suit pas la convention (ex. `2026-05-07_1100_<id-court>.md`), proposer un renommage à l'utilisateur avant de clôturer la skill. Mettre à jour `<meeting-notes>/.transcripts-ingested.json` (`target_note`) si l'utilisateur valide le renommage.
11. **Mettre à jour les fiches `Entities/` impactées** si la réunion a fait émerger une nouvelle info structurante : nouvel email, nouveau rôle, nouvel alias de transcription récurrent. Pour une **nouvelle entité** (personne, organisation, produit, concept) jamais fichée : déclencher `/ficher <nom>` plutôt que de l'ajouter sauvagement à la note.
12. **Cleanup de la source inbox tierce** (optionnel, prompté) : si le frontmatter de la note contient `source_kind: inbox_local` + `source_inbox_path`, proposer en y/N la suppression du fichier brut original. Source de vérité : le frontmatter de la note corrigée. Ne pas supprimer dans ces cas : la note est dans `<meeting-notes>/À router/` (routage non résolu), l'utilisateur a passé `--no-correction` en amont, ou aucun compte-rendu n'a été validé.

## Convention de nommage des notes (pour le renommage à l'étape 10)

Format cible : `[Participant 1] x [Participant 2] x [...] - JJ.MM.AAAA.md`

- **Participants** : un par personne effectivement présente (cf. `attendees` du frontmatter, déduplicé des invités absents). Format `Prénom Nom` (et éventuellement société pour les externes : `Alice Martin OrgX`, `Bob Dupont CEA`). Inclure `<Toi>` à la fin si pertinent.
- **Date** : `JJ.MM.AAAA` (jour-mois-année avec points), basée sur `event_start`.
- **Exemples valides** :
  - `Alice Martin x <Toi> - 06.05.2026.md`
  - `Charlie Durand OrgX x <Toi> - 07.05.2026.md`
  - `Alice x Bob x Charlie x <Toi> - 06.05.2026.md`
- **Exceptions — ne pas renommer** :
  - Notes dans un dossier de série existant avec sa propre convention (`<meeting-notes>/<Prénom> x <Toi>/SXX.md`, `<meeting-notes>/<Synchro>/Hebdo SXX.md`, etc.)
  - Notes que l'utilisateur a explicitement nommées différemment

Proposer toujours, ne pas renommer silencieusement.

## Récupération du contexte des notes collaboratives (optionnel)

Si tu utilises un outil de notes collaboratives en réunion (Docs, Notion, HackMD, etc.), il contient souvent des sujets discutés, décisions, et noms propres écrits correctement. C'est un complément précieux au transcript audio brut.

### Convention suggérée

Pour chaque dossier de notes de réunion, placer un fichier `_docs.md` (ou équivalent) qui décrit :
- L'identifiant ou l'URL du document parent regroupant les notes de la série
- La convention de nommage des sous-documents (ex. `DD/MM (SXX)`, `DD/MM`, `D mois` en français)

### Étapes

1. **Vérifier l'existence d'un `_docs.md`** dans le dossier de la note traitée
2. **Lire le `_docs.md`** pour récupérer l'identifiant parent et la convention de nommage
3. **Lister les sous-documents** via le MCP / l'API approprié
4. **Trouver le sous-document de la session** selon la convention :
   - `DD/MM (SXX)` → matching direct sur SXX dans le titre
   - `DD/MM` ou `D mois` (français) → convertir SXX → date du lundi de la semaine ISO de l'année courante. Si besoin : `python3 -c "from datetime import date; print(date.fromisocalendar(<année>, <SXX>, 1).strftime('%-d/%m'))"`
   - Filtrer les annexes hors-CR (priorisations, rapports, TODO, dossiers d'archives)
5. **Récupérer le contenu** du sous-document
6. Si plusieurs sous-documents candidats ou aucun match clair : demander à l'utilisateur quel sous-document utiliser plutôt que de deviner

### Usage du contexte

- **Speakers** : si les notes listent les participants, l'utiliser pour résoudre les SPEAKER_XX
- **Noms propres / acronymes** : prioriser l'orthographe des notes collaboratives (validée par les rédacteurs) sur celle du transcript audio
- **Compte-rendu** : les notes collaboratives contiennent souvent déjà les points clés / décisions / actions sous forme structurée — s'appuyer dessus, ne pas réinventer
- **Vérification** : si une décision ou action mentionnée dans le transcript audio n'apparaît pas du tout dans les notes, la marquer dans le compte-rendu mais signaler à l'utilisateur

## Checkpoint d'incertitude (étape 4 — obligatoire)

Avant d'appliquer la moindre correction au transcript, lister en une passe tous les éléments dont la confiance est inférieure à 90 %, groupés par catégorie. **Ne pas écrire la correction tant que l'utilisateur n'a pas validé / corrigé cette liste.**

### Format de sortie strict

```
## Checkpoint d'incertitude (à valider avant correction)

### Speakers (<90% confiance)
- SPEAKER_00 → Alice Martin (~75%) — base : présentation "Alice, lead produit" + tour de table notes
- SPEAKER_02 → ??? — base : aucun indice direct

### Noms propres (<90% confiance)
- "Camille Lambert" → vérifier orthographe (~60%) — base : pas dans les référentiels, prononciation possible "Lamberg"
- "AcmeProduct" vs "Acme Product" (~80%) — base : transcript audio ambigu, notes ne tranchent pas

### Intentions / décisions (<90% confiance)
- "Décision : freeze sur ProjetX" (~70%) — base : phrase incomplète dans le transcript, notes ne mentionnent pas, à reconfirmer
- "Action : envoyer le deck d'ici lundi" — assignée à @Bob ou @Charlie ? (~50%)

**En attente de validation utilisateur avant d'appliquer les corrections.**
```

### Règles

- Si **aucun** élément n'est <90 %, écrire explicitement "Aucune incertitude majeure — je peux procéder directement" et attendre quand même un GO court.
- Pour chaque item : `valeur — confiance estimée — base d'évidence` (notes collaboratives, transcript, référentiel, calendrier, hypothèse).
- Catégories : **Speakers**, **Noms propres** (personnes / entreprises / produits), **Intentions / décisions / actions**. Omettre une catégorie si vide.
- Ne pas confondre "incertitude" et "ambiguïté résolue" : une fois validé par l'utilisateur, ne pas re-poser la question.

## Règle critique : direction des données

Cette skill **lit** depuis les notes collaboratives et **écrit** dans la note locale. Jamais l'inverse. Si tu es tenté de proposer de republier le résultat vers la source des notes collaboratives : **stop**, ce n'est pas le rôle de cette skill.

## Structure finale du document

```markdown
## Compte-rendu de la réunion

### Points clés
- ...

### Décisions
- ...

### Actions
- [ ] Action — @Responsable

## Transcript de la réunion
[transcript corrigé avec vrais noms]
```

## Règles pour le compte-rendu

- Style concis, orienté action
- Nommer les personnes impliquées dans chaque point/décision/action
- Les actions doivent être assignées à quelqu'un (format `@Prénom`)
- Si aucune décision formelle n'a été prise, omettre la section "Décisions"
- Si aucune action n'a été identifiée, omettre la section "Actions"

## Référentiels personnels

> ⚠️ **À personnaliser.** Cette section doit contenir tes propres tableaux de noms propres, acronymes et produits à corriger systématiquement. Plus la liste est précise, meilleure est la correction.
>
> Si ton vault suit le [pattern Karpathy](../../docs/karpathy-pattern.md), la source canonique de vérité pour personnes / organisations / produits / concepts est `Entities/Index.md` (ou `Entités/Index.md`). Plutôt que de dupliquer la liste ici, charger l'index puis lire les fiches `Entities/.../Nom.md` concernées (la section "Notes" de chaque fiche liste les déformations de transcription courantes). Conserver dans ce SKILL.md la quick-ref des **acronymes universels** et **règles de casse** (toujours utiles, indépendantes du domaine), plus un mini-tableau de l'équipe directe pour résolution rapide des speakers.

### Format suggéré

#### Personnes (équipe, contacts récurrents)

| Fonction | Nom correct |
|----------|-------------|
| ... | Prénom Nom |

#### Organisations et acronymes

| Nom correct | Graphies incorrectes fréquentes | Signification |
|-------------|---------------------------------|---------------|
| ACME | acme, A.C.M.E. | Définition de l'acronyme |

#### Produits / projets

| Nom correct | Graphies incorrectes fréquentes | Description |
|-------------|---------------------------------|-------------|
| MonProduit | mon produit, MON PRODUIT | Description courte |

#### Concepts techniques

| Nom correct | Graphies incorrectes fréquentes |
|-------------|---------------------------------|
| MCP | mcp, M.C.P. |
| RAG | rag, R.A.G. |
| LLM | llm, L.L.M. |

## Règles de correction

1. **Casse des acronymes** : toujours en majuscules par défaut (sauf casse spécifique du produit)
2. **Noms de produits** : respecter la casse exacte (ex. `iPhone`, `eBay`, `LIAne`)
3. **Prénoms composés** : conserver les tirets (Anna-Livia, Jean-François)
4. **Accents** : les rétablir (Nathanaël, Stéphanie, Jérémie)
5. **Particules** : respecter la casse selon les conventions du nom (Le Duc, Di Benedetto, El-Mnebhi, van der Berg)

## Exemple d'utilisation

**Input :**
> Réunion avec jean francois durand et marie le duc sur le projet acme. Discussion sur l'intégration mcp.

**Output (avec référentiels personnalisés) :**
> Réunion avec Jean-François Durand et Marie Le Duc sur le projet ACME. Discussion sur l'intégration MCP.
