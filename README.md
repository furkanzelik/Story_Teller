# Verhaaltjesmaker — AI bedtime storyteller

Monorepo:

| Pad         | Wat                                            |
|-------------|------------------------------------------------|
| `app/`      | Flutter-client (Riverpod + go_router)          |
| `backend/`  | FastAPI + PostgreSQL (SQLAlchemy 2.0, Alembic)  |
| `docs/`     | Stappenplan en architectuurnotities            |

## Harde eisen (gelden voor elke fase)

1. Elke gegenereerde verhaaltekst gaat door een **moderatie-check** vóór hij de
   client bereikt (geen geweld/enge content, leeftijdsgeschikt, positieve
   afloop). In de DB afgedwongen via `stories.moderation_status`; de API geeft
   nooit een niet-goedgekeurd verhaal terug.
2. **Ouder-gate** (rekensom) vóór instellingen en betaalscherm.
   Client: `Routes.gated` in `app/lib/src/router/app_router.dart`.
3. Geen tracking/advertenties gericht op kinderen.
4. Geen in-app aankopen die het kind zelf kan doen — alleen ouder-abonnement.

## Status — Fase 1 (fundament) ✅

- [x] Flutter-projectstructuur, navigatie, state management (Riverpod)
- [x] FastAPI-skeleton, lokaal draaiend (`/health`, `/me`, `/topics`, `/stories`)
- [x] PostgreSQL-schema: `users`, `topics`, `stories`, `subscriptions`,
      `usage_events` (Alembic `0001_initial`)
- [x] Auth (Supabase): e-mail OTP-login in de app, JWT-verificatie +
      `users`-upsert in de backend, `Authorization: Bearer` op elke API-call

## Status — Fase 2 (het verhaal) ✅

- [x] `POST /stories/generate`: topic + leeftijd → Claude Haiku 4.5 → verhaal
- [x] Moderatie-stack (hard-eis 1): blocklist + Claude-classifier, **faalt
      gesloten**; bij afkeuring 1× opnieuw genereren, anders 422 + `rejected`-rij
- [x] Verhaalscherm in de app: laadstatus, verhaal, "opnieuw genereren", nette
      foutmeldingen

Zet `ANTHROPIC_API_KEY` in `backend/.env` (console.anthropic.com → API keys).

## Status — Fase 3 (voorleesaudio) ✅

- [x] TTS via **Piper** (open-source, offline, gratis — geen account/key). Stem
      `nl_NL-pim-medium`. Provider-onafhankelijk (`services/tts.py`): later
      `TTS_PROVIDER=elevenlabs` + key voor premium stemkwaliteit.
- [x] `POST /stories/{id}/audio` → synth → mp3 gecacht in `backend/media/`,
      geserveerd via `/media` (range requests).
- [x] `just_audio`-speler in de app: play/pause, voortgangsbalk, laadt
      automatisch zodra de verhaaltekst er is.

Eerste keer: `./scripts/fetch_piper_voice.sh` in `backend/` om de stem
(~60MB, git-ignored) te downloaden.

**Volgende: Fase 4** — opslaan & bibliotheek.

### Supabase-dashboard (eenmalig instellen)

1. **Authentication → Providers → Email**: aan laten staan.
2. **Authentication → Email Templates → "Magic Link"**: zorg dat de template
   `{{ .Token }}` bevat (de 6-cijferige code), niet alleen `{{ .ConfirmationURL }}`.
   De app gebruikt code-invoer, geen deep link.
3. **Project Settings → API → JWT Settings**: kopieer "JWT Secret" naar
   `backend/.env` als `SUPABASE_JWT_SECRET`.

## Snel starten

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

docker compose up -d          # Postgres op :5432  (vanuit repo-root)
alembic upgrade head
python -m scripts.seed_topics
uvicorn app.main:app --reload # http://localhost:8000/docs
```

### App
```bash
cd app
cp assets/.env.example assets/.env   # zet API_BASE_URL goed
flutter pub get
flutter run
```

Zie `docs/plan.md` voor het volledige stappenplan.
