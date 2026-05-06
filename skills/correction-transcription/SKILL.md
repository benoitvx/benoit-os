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
4. Remplacer les `SPEAKER_XX` par les vrais prénoms/noms dans tout le transcript
5. Corriger les erreurs (noms mal orthographiés, acronymes incorrects) en utilisant les référentiels personnels (voir section ci-dessous) **et les noms propres/acronymes présents dans les notes collaboratives**
6. Ajouter le titre `## Transcript de la réunion` au-dessus du transcript corrigé
7. Générer un `## Compte-rendu de la réunion` en début de note, en croisant transcript corrigé **et notes collaboratives** (les notes collaboratives reflètent les décisions/actions formalisées)
8. Écrire le résultat final **dans la note locale uniquement** — ne pas republier vers la source des notes collaboratives

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
