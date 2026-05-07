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
| Notes collaboratives — outil de visio auto-transcrit | racine ou dossier dédié, exposé via un MCP `docs` | ex. `Réunion "<id>" du <YYYY-MM-DD> à <HH:MM>` |
| Notes collaboratives — outil d'enregistrement IRL | racine ou dossier dédié, exposé via un MCP `docs` | ex. `Enregistrement <DD/MM/YYYY>, <HH:MM>` |
| Inbox tierce (Granola, Alter, Otter, Read.ai…) | `<meeting-notes>/Inbox/` dans ton vault local | Frontmatter `start_time` ISO, sinon mtime fichier |

> Adapter les patterns ci-dessus à ton propre vault / système de notes. La skill peut détecter **plusieurs patterns en parallèle** côté docs : déclare-les comme des regex avec leur logique d'extraction `(meeting_id, datetime_iso)` et un `source_kind` distinct (ex. `docs_visio`, `docs_transcript_irl`, `inbox_local`).

## Workflow

### 1. Canary — vérifier les accès

- Vérifier l'accès au système de notes collaboratives (équivalent `docs_get_me` selon le MCP utilisé).
- Si erreur d'auth : afficher "Reconnexion requise — mettre à jour le cookie / token et relancer." et stopper.

### 2. Découverte

> **Cutoff par défaut : 48 h.** Sans ça, la skill remonte des transcripts pré-existant la mise en place du pipeline, ce qui produit du bruit. Exposer un argument `--since 24h|7d|...` ou `--all` pour désactiver.

**Notes collaboratives** — privilégier la **recherche server-side ciblée** (équivalent `docs_search_documents`) sur un mot-clé du pattern, plutôt que de paginer tout le top-level :

```
docs_search_documents(query="Réunion", page_size=20)
docs_search_documents(query="Enregistrement", page_size=20)
```

Pour chaque résultat, dans cet ordre :

1. **Filtre cutoff** : skip si `updated_at < now - cutoff`. Les résultats étant triés par `updated_at` desc, on peut abandonner la pagination dès qu'un résultat plus vieux apparaît.
2. **Filtre regex strict** sur le titre, **un par outil de transcription** :
   - `^Réunion "([^"]+)" du (\d{4}-\d{2}-\d{2}) à (\d{2}:\d{2})$` → `source_kind: docs_visio`, `meeting_id` = slug, datetime depuis groupes 2+3
   - `^Enregistrement (\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2})$` → `source_kind: docs_transcript_irl`, `meeting_id` = doc UUID, datetime parsé via `strptime("%d/%m/%Y %H:%M")`

Toujours stocker un `source_kind` distinct par pattern, ça simplifie le routage et la déduplication.

**Inbox tierce** :
- `ls <meeting-notes>/Inbox/*.md` (ignorer `_README.md` et `.gitkeep`).
- Appliquer le **même cutoff** sur le `mtime` du fichier.
- Pour chaque fichier dans le cutoff : lire le frontmatter ; si `start_time` présent → utiliser ; sinon `os.path.getmtime` → ISO local.

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

**Réunions ad-hoc / non-récurrentes** (pas de série dédiée) :

1. Si **2 attendees** ET un dossier 1:1 existe (`<meeting-notes>/<Prénom> x <Toi>/`) → router dedans avec la convention de la série existante.
2. Si **>2 attendees** OU pas de dossier 1:1 correspondant → **NE PAS** shoehorner dans un dossier 1:1 existant. Proposer à la place :
   - **Convention de nommage** : `[Participant 1] x [Participant 2] x [...] - JJ.MM.AAAA.md` (cf. ci-dessous).
   - Dossier par défaut : `<meeting-notes>/Ad-hoc/`. Demander confirmation avant de créer le dossier s'il n'existe pas. L'utilisateur peut aussi router vers un autre emplacement (ex. `<projects>/<projet>/Meetings/`).
3. **Aucun match calendrier** : fallback technique `<meeting-notes>/À router/<YYYY-MM-DD>_<HHMM>_<id-court>.md` (l'utilisateur renommera selon la convention au moment du routage).

##### Convention de nommage `[Participant 1] x [Participant 2] x [...] - JJ.MM.AAAA.md`

- **Participants** : un par attendee non-`<Toi>`, format `Prénom Nom` (et éventuellement la société pour les externes : `Alice Martin OrgX`, `Bob Dupont CEA`). Inclure `<Toi>` à la fin si pertinent (`... x <Toi>`).
- **Date** : `JJ.MM.AAAA` (jour-mois-année avec points), basée sur `event_start`.
- **Génération automatique** : extraire les prénoms depuis les `attendees` (emails) et proposer un nom à valider, plutôt que deviner les noms de famille / sociétés. Si un attendee est uniquement représenté par son email (pas dans le référentiel personnel), demander à l'utilisateur de préciser (`Prénom Nom` ou `Prénom Nom Société`).
- **Exemples valides** :
  - `Alice Martin x <Toi> - 06.05.2026.md`
  - `Bob Dupont CEA x <Toi> - 29.04.2026.md`
  - `Charlie Durand OrgX x <Toi> - 07.05.2026.md`
  - `Alice x Bob x Charlie x <Toi> - 06.05.2026.md`
- **Si la cible est un dossier de série existant avec sa propre convention** (`<meeting-notes>/<Prénom> x <Toi>/SXX.md`, `<meeting-notes>/<Hebdo>/Hebdo SXX.md`, etc.) : conserver la convention de la série, ne pas appliquer celle-ci.

Calculer le **numéro de semaine ISO** depuis `start` : `python3 -c "from datetime import date; print(date.fromisoformat('<YYYY-MM-DD>').isocalendar().week)"`.

#### 4.c. Confirmation utilisateur

Présenter en une ligne :
```
Match : "Synchro projet X" du 2026-05-04 10:00 → <meeting-notes>/Synchro projet X/Hebdo S19.md
   ↳ Series confiance: 95%   ↳ Semaine ISO confiance: 100%
OK ? [validate / change-series / change-week / change-name / skip]
```

Pour une réunion ad-hoc (cas 2 ci-dessus), la ligne devient :
```
Match : "Projet Y x OrgX" du 2026-05-07 11:00 → <meeting-notes>/Ad-hoc/Alice Martin OrgX x <Toi> - 07.05.2026.md
   ↳ Nom proposé depuis attendees (à confirmer/amender si noms de famille manquants)
OK ? [validate / change-folder / change-name / skip]
```

Si réponse autre que "validate" : laisser l'utilisateur corriger nom et/ou dossier avant de continuer.

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
source_kind: docs_visio|docs_transcript_irl|inbox_local
source_doc_id: <id>                # si source_kind commence par docs_
source_doc_meeting_id: <slug>      # si source_kind=docs_visio uniquement
source_inbox_path: <path>          # si source_kind=inbox_local
ingested_at: <ISO now>
---

## Transcript brut (à corriger)

<contenu brut>
```

Pour la source notes collaboratives : récupérer le contenu via le MCP/API approprié.

#### 4.e. Délégation à `correction-transcription` (automatique)

**Par défaut : enchaîner immédiatement** la skill `correction-transcription` dans la même session, sans demander à l'utilisateur de relancer une commande. La note brute vient d'être créée → la correction est l'étape suivante évidente, pas une décision à reporter.

Workflow déclenché :
- Lire la note (étape 1)
- Récupérer le contexte des notes collaboratives liées (étape 2) — utiliser `_docs.md` du dossier série + le frontmatter de la note (attendees, summary)
- Identifier les speakers (étape 3) — exploiter `attendees` du frontmatter
- **Checkpoint d'incertitude étape 4 (obligatoire)** — voir `correction-transcription/SKILL.md`. Là, et seulement là, l'utilisateur reprend la main pour valider la liste d'incertitudes.
- Procéder aux étapes 5-9 après validation du checkpoint

**Exception — ne pas enchaîner** dans ces cas :
- L'utilisateur a passé `--no-correction` à `/ingerer-transcripts` (mode dry-run / batch-ingest sans correction).
- La note cible est dans un dossier "À router" (routage non résolu, pas la peine de corriger un truc dont on ne sait pas encore où il va).
- L'ingestion est dans une boucle multi-transcripts (>1 candidat) : ingérer tout, puis enchaîner les corrections une par une à la fin **uniquement après confirmation utilisateur** (sinon ça noie l'utilisateur dans des checkpoints d'incertitude empilés).

Si on **n'enchaîne pas**, terminer en signalant explicitement : "Note brute créée. Lance `/correction-transcription` sur cette note quand tu veux la traiter." (cas explicite, pas le défaut).

#### 4.f. Mise à jour state file

Une fois la correction validée (ou la note brute créée si l'utilisateur veut différer la correction), mettre à jour `<meeting-notes>/.transcripts-ingested.json` :

```json
{
  "schema_version": 1,
  "docs": {
    "<doc_id>": {
      "source_kind": "docs_visio",
      "ingested_at": "<ISO>",
      "target_note": "<meeting-notes>/Synchro projet X/Hebdo S19.md",
      "event_summary": "Synchro projet X"
    },
    "<other_doc_id>": {
      "source_kind": "docs_transcript_irl",
      "ingested_at": "<ISO>",
      "target_note": "<meeting-notes>/.../<note>.md",
      "event_summary": "..."
    }
  },
  "inbox": {
    "<meeting-notes>/Inbox/2026-05-06_meet.md": {
      "source_kind": "inbox_local",
      "ingested_at": "<ISO>",
      "sha256": "...",
      "target_note": "...",
      "event_summary": "..."
    }
  }
}
```

Le bucket `docs` regroupe tous les `source_kind` qui commencent par `docs_` (visio, transcript IRL, etc.). La déduplication se fait par UUID, le `source_kind` interne sert au routage et au récap.

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
