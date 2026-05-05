---
name: pause-session
description: Sauvegarde l'état de la session Claude Code courante dans `Sessions Claude/index.md` à la racine du projet pour permettre une reprise ultérieure via `claude --resume [id]`. Stocke ID de session, objectif, état actuel, prochaine étape et fichiers touchés. À la reprise, propose de supprimer l'entrée correspondante de l'index. Utiliser quand l'utilisateur dit "pause cette session", "sauvegarde la session", "/pause-session", ou doit interrompre son travail Claude Code et veut pouvoir reprendre plus tard.
---

# pause-session

Sauvegarde l'état de la session Claude Code courante pour reprise via `claude --resume <id>`.

## Workflow

### 1. Récupérer l'ID de la session courante

Exécuter le script :

```bash
bash ~/.claude/skills/pause-session/scripts/get_session_id.sh
```

Il retourne l'UUID sur stdout. Si erreur, signaler à l'utilisateur et arrêter.

### 2. Lire l'index existant (s'il existe)

Chemin : `<cwd>/Sessions Claude/index.md`

Si le fichier existe, lire son contenu. Chercher si l'ID de session y figure (les entrées sont marquées par `<!-- session: <uuid> -->`).

### 3. Brancher selon le cas

#### Cas A — La session courante est déjà dans l'index (= l'utilisateur reprend)

L'utilisateur a fait `claude --resume <id>` et invoque la skill : il vient de reprendre.

1. Afficher l'entrée existante (objectif, état, prochaine étape) pour rappel.
2. Demander : « Tu reprends cette session — je supprime l'entrée de l'index ? »
3. Si oui, supprimer le bloc complet de l'entrée (du marqueur `<!-- session: <uuid> -->` jusqu'au séparateur `---` suivant exclu, et le `---` qui le précède).
4. Si l'index ne contient plus aucune entrée, supprimer le fichier `index.md` (et le dossier `Sessions Claude/` s'il est vide).

#### Cas B — Session non présente (= sauvegarde initiale)

1. **Créer le dossier** `Sessions Claude/` à la racine du projet (cwd) s'il n'existe pas.
2. **Si projet git** (présence de `.git/` ou `git rev-parse --git-dir` réussit), s'assurer que `Sessions Claude/` est dans `.gitignore` :
   - Lire `.gitignore` (ou créer s'il n'existe pas)
   - Si la ligne `Sessions Claude/` (ou `Sessions Claude`) n'y figure pas, l'ajouter à la fin
3. **Construire le résumé structuré** depuis le contexte de la conversation :
   - **Objectif** : ce que l'utilisateur essaie d'accomplir (1 phrase)
   - **État actuel** : où on en est concrètement, ce qui a été fait
   - **Prochaine étape** : la toute prochaine action à reprendre
   - **Fichiers touchés** : liste des fichiers créés/modifiés pendant la session (avec chemins absolus ou relatifs au projet)
4. **Montrer un aperçu** de l'entrée à l'utilisateur avant écriture, lui laisser corriger.
5. **Écrire** dans `Sessions Claude/index.md` (créer si besoin, sinon insérer en haut sous le titre, avant les autres sessions).

## Format de l'index

```markdown
# Sessions Claude

Sessions Claude Code en pause. Reprendre avec `claude --resume <id>`.

---

<!-- session: 696d7418-5fd0-4d7a-a03a-849f36d67089 -->
## 2026-04-30 14:32 — Refactor du module auth

- **ID** : `696d7418-5fd0-4d7a-a03a-849f36d67089`
- **Reprendre** : `claude --resume 696d7418-5fd0-4d7a-a03a-849f36d67089`
- **Objectif** : Extraire la logique JWT dans un service dédié
- **État actuel** : `JwtService` créé, tests verts. Reste à brancher dans `AuthController`.
- **Prochaine étape** : Remplacer les appels directs à `jwt.sign` par `jwtService.sign` dans `src/auth/AuthController.ts`
- **Fichiers touchés** :
  - `src/auth/JwtService.ts` (nouveau)
  - `src/auth/JwtService.test.ts` (nouveau)
  - `src/auth/AuthController.ts` (à modifier)

---

<!-- session: <autre-uuid> -->
## ...
```

Les nouvelles entrées sont insérées **en haut** (juste après le `---` qui suit l'intro), pour avoir les sessions les plus récentes en premier.

## Notes d'implémentation

- Le marqueur HTML `<!-- session: <uuid> -->` permet de retrouver et supprimer une entrée de manière déterministe — toujours l'inclure.
- Le titre de la section (ex. « Refactor du module auth ») doit être un résumé court (5-8 mots) tiré de l'objectif.
- La date est en local (format `YYYY-MM-DD HH:MM`).
- Pour la détection git, `git rev-parse --is-inside-work-tree 2>/dev/null` suffit.
- Si le résumé structuré nécessite des infos manquantes du contexte (ex. skill invoquée très tôt), demander brièvement avant de sauvegarder.
