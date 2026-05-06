---
name: ingerer-transcripts
description: "Pipeline d'ingestion de transcripts de réunion : détecte les nouveaux transcripts bruts (depuis un système de notes collaboratives type La Suite Docs / Notion / etc., ou un dossier d'inbox alimenté par un outil tiers comme Granola), matche chaque transcript à un calendrier (flux iCal en lecture seule), route vers le bon dossier `<meeting-notes>/<series>/`, puis délègue la correction à la skill `correction-transcription`. Triggers: /ingerer-transcripts, 'ingérer transcripts', 'pipeline transcripts'."
---

# Ingestion + correction de transcripts (pipeline)

## Objectif

Automatiser la chaîne **détection → routage → ingestion → correction** des transcripts de réunion, sans copier-coller manuel.

## Sources de transcripts

Cette skill suppose deux sources possibles, à activer selon ton setup :

| Source | Localisation typique | Format de titre / fichier |
|---|---|---|
| Notes collaboratives (Docs/Notion/HackMD/…) | racine ou dossier dédié, exposé via un MCP `docs` | `Réunion "<id>" du <YYYY-MM-DD> à <HH:MM>` (ou pattern équivalent à régler) |
| Inbox tierce (Granola, Otter, Read.ai…) | `<meeting-notes>/Inbox/` dans ton vault local | Frontmatter `start_time` ISO, sinon mtime fichier |

> Adapter les conventions ci-dessus à ton propre vault / système de notes.

## Workflow

### 1. Canary — vérifier les accès

- Vérifier l'accès au système de notes collaboratives (équivalent `docs_get_me` selon le MCP utilisé).
- Si erreur d'auth : afficher "Reconnexion requise — mettre à jour le cookie / token et relancer." et stopper.

### 2. Découverte

**Notes collaboratives** :
- Lister les documents top-level (équivalent `docs_list_documents` sans `parent_id`).
- Filtrer côté client sur le pattern de titre du transcript brut configuré.
- Extraire `(meeting_id, datetime_iso)` du titre.

**Inbox tierce** :
- `ls <meeting-notes>/Inbox/*.md` (ignorer `_README.md` et `.gitkeep`).
- Pour chaque fichier : lire le frontmatter ; si `start_time` présent → utiliser ; sinon `os.path.getmtime` → ISO local.

### 3. Filtre déjà-ingérés

Lire `<meeting-notes>/.transcripts-ingested.json` :
- Pour notes collaboratives : skip si `doc_id` déjà présent.
- Pour inbox tierce : skip si `relpath` présent ET hash SHA256 actuel == celui stocké (sinon = mise à jour, ré-ingérer en mode update).

Si plus rien à ingérer : afficher "Aucun nouveau transcript à ingérer." et stopper.

### 4. Boucle utilisateur — un transcript à la fois

Pour chaque candidat (par ordre chronologique croissant) :

#### 4.a. Match calendrier

```bash
python3 <skill-dir>/bin/caldav_lookup.py \
  --datetime <ISO> --window 15
```

Le script renvoie un JSON :
```json
{
  "matched": true,
  "summary": "Synchro projet X",
  "start": "2026-05-04T10:00:00+02:00",
  "end": "2026-05-04T10:30:00+02:00",
  "uid": "abc@example.org",
  "attendees": ["alice@acme.org", "bob@acme.org"],
  "rrule": "FREQ=WEEKLY;BYDAY=MO"
}
```

Si `matched: false` ou `summary` ambigu : demander confirmation (3-4 candidats max).

#### 4.b. Mapping série

Comparer le `summary` de l'event aux séries connues. Source de vérité par ordre de priorité :

1. Les `_docs.md` présents dans chaque sous-dossier de `<meeting-notes>/` (frontmatter `docs_parent_id`, `naming_local`, etc.).
2. Heuristique nom de dossier : matcher `summary` en lower-case + suppression accents contre les noms de sous-dossiers.

Si aucun match : fallback `<meeting-notes>/Inbox/<datetime>_<id>.md` (ou note temp dans `<meeting-notes>/À router/`).

Calculer le **numéro de semaine ISO** depuis `start` : `python3 -c "from datetime import date; print(date.fromisoformat('<YYYY-MM-DD>').isocalendar().week)"`.

#### 4.c. Confirmation utilisateur

Présenter en une ligne :
```
Match : "Synchro projet X" du 2026-05-04 10:00 → <meeting-notes>/Synchro projet X/Hebdo S19.md
   ↳ Series confiance: 95%   ↳ Semaine ISO confiance: 100%
OK ? [validate / change-series / change-week / skip]
```

Si réponse autre que "validate" : laisser l'utilisateur corriger avant de continuer.

#### 4.d. Création de la note cible

Si la note existe déjà ET contient une section `## Transcript` ou `## Transcript brut` : **abort** ce transcript, signaler à l'utilisateur, ne pas écraser.

Sinon, créer (ou compléter) avec :

```markdown
---
event_uid: <uid>
event_summary: <summary>
event_start: <ISO>
event_end: <ISO>
duration_minutes: <int>
attendees: [<email>, <email>]
source: docs|inbox
source_doc_id: <id>            # si source=docs
source_inbox_path: <path>      # si source=inbox
ingested_at: <ISO now>
---

## Transcript brut (à corriger)

<contenu brut>
```

Pour la source notes collaboratives : récupérer le contenu via le MCP/API approprié.

#### 4.e. Délégation à `correction-transcription`

Inviter l'utilisateur à lancer `/correction-transcription` sur la note créée — OU enchaîner directement en chargeant la skill `correction-transcription` dans la même session, qui va alors :
- Lire la note (étape 1)
- Récupérer le contexte des notes collaboratives liées (étape 2) — utiliser `_docs.md` du dossier série
- Identifier les speakers (étape 3) — exploiter `attendees` du frontmatter
- **Checkpoint d'incertitude étape 4 (obligatoire)** — voir `correction-transcription/SKILL.md`
- Procéder aux étapes 5-9 après validation utilisateur

#### 4.f. Mise à jour state file

Une fois la correction validée (ou la note brute créée si l'utilisateur veut différer la correction), mettre à jour `<meeting-notes>/.transcripts-ingested.json` :

```json
{
  "schema_version": 1,
  "docs": {
    "<doc_id>": {
      "ingested_at": "<ISO>",
      "target_note": "<meeting-notes>/Synchro projet X/Hebdo S19.md",
      "event_summary": "Synchro projet X"
    }
  },
  "inbox": {
    "<meeting-notes>/Inbox/2026-05-06_meet.md": {
      "ingested_at": "<ISO>",
      "sha256": "...",
      "target_note": "...",
      "event_summary": "..."
    }
  }
}
```

### 5. Récap final

Après la boucle, afficher :
```
✅ Ingérés : N transcripts
   - <meeting-notes>/Synchro projet X/Hebdo S19.md (depuis docs)
   - <meeting-notes>/1:1 Alice/S18.md (depuis inbox)
⏭️  Skipés : K (déjà ingérés ou en attente de routage)
⚠️  Problèmes : ...
```

## Règles dures

- **Lecture seule côté notes collaboratives** : ne jamais appeler de `*_create_*`, `*_update_*`, `*_delete_*`. Cette skill **lit** depuis le système de notes et **écrit** dans le vault local.
- **Lecture seule côté CalDAV/iCal** : le script `caldav_lookup.py` ne fait que des `GET` ; pas d'écriture / création / suppression d'event.
- **Idempotence** : un re-run immédiat de `/ingerer-transcripts` ne doit produire aucune action.
- **Un transcript à la fois** : pas de parallélisation. L'utilisateur valide chaque routage.
- **Pas d'écrasement silencieux** : si la note cible existe déjà avec un transcript, abort + signal.

## Cas d'erreur attendus

| Erreur | Action |
|---|---|
| Auth notes collaboratives expirée | Stop, demander reconnexion |
| Pas de match calendrier | Lister 3 alternatives proches, ou fallback inbox |
| `caldav_lookup.py` plante (réseau, auth) | Afficher l'erreur, proposer mode dégradé : routage manuel |
| Note cible déjà transcrite | Skip, signaler |
| Inbox tierce : fichier sans `start_time` ni mtime exploitable | Demander à l'utilisateur de saisir la date |

## Configuration requise

Variables d'environnement (à poser dans `~/.claude/settings.json` → bloc `env`, ou dans un `.env` lu par tes scripts) :

- `CALDAV_ICS_URL` (requis) : URL du flux iCal `text/calendar` exposé par ton calendrier (lecture seule). Beaucoup de plateformes (OX App Suite, Google Calendar, iCloud, etc.) proposent un partage public de ce type sans credentials.
- `CALDAV_USERNAME` / `CALDAV_PASSWORD` (optionnels) : pour basic auth si le flux la requiert.

Dépendances Python (auto-gérées via `uv run --with ...`, installation à la première exécution) :
- `icalendar` (parsing ICS)
- `recurring-ical-events` (expansion des règles RRULE pour les meetings récurrents)
- `python-dateutil`
- `httpx` (fetch HTTP)

## Personnalisation

Cette skill est un squelette. Pour la rendre opérationnelle, tu dois :

1. **Configurer un MCP de notes collaboratives** (ex. `la-suite-docs`, Notion MCP, etc.) qui expose `list_documents`, `get_document_content`.
2. **Adapter le pattern de titre** des transcripts bruts à ce que ton outil produit (ex. La Suite Docs → `Réunion "<id>" du <date> à <heure>`).
3. **Définir tes conventions de dossiers** pour `<meeting-notes>/` (mémoires de réunions) et `Inbox/` (drop d'outils tiers comme Granola).
4. **Créer un `_docs.md` par série** dans `<meeting-notes>/<série>/` qui mappe la série au document parent et à la convention de nommage.
5. **Renseigner `CALDAV_ICS_URL`** avec ton flux iCal personnel.

## Pointeurs

- Skill aval : `correction-transcription` (ne pas dupliquer la logique de correction)
- État : `<meeting-notes>/.transcripts-ingested.json`
- Helper CalDAV/iCal : `<skill-dir>/bin/caldav_lookup.py`
