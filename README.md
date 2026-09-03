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

## Status — Fase 4 (bewaren & bibliotheek) ✅

- [x] `PUT /stories/{id}/saved` + hartje op het verhaalscherm (optimistisch).
- [x] `GET /stories` = de bibliotheek (alleen saved + approved, per user);
      `GET /stories/{id}` om te heropenen. Autorisatie centraal in
      `_get_owned_story` — andermans verhaal → 404 (geen bestaans-oracle).
- [x] Bibliotheekscherm in de app: lijst, emoji per onderwerp, audio-indicator,
      tik om te heropenen (tekst + audio, geen "opnieuw").
- [x] **Rate limiting** (`services/rate_limit.py`, via `usage_events`):
      20 generaties + 40 audio per gebruiker per uur.

### Beveiliging — voor productie nog doen

- `assets/.env` in de app: `DEBUG_LOGGING=false` in release builds.
- Backend prod: **geen** `ENVIRONMENT`/`DEBUG` env → defaults zijn al veilig
  (`production`, geen `/docs`, geen SQL-echo). API alleen via HTTPS.
- `/media/*` audio staat nu achter een onraadbare UUID maar zonder auth —
  vóór launch achter een auth-check of signed URL zetten. Geen opschoning van
  oude bestanden/niet-bewaarde verhalen (toevoegen).
- Security headers (HSTS etc.) via reverse proxy.

## Status — Fase 5 (monetization) ◑

- [x] **Gratis-laag limiet**: 2 verhalen per kalenderweek (ma 00:00 UTC) voor
      niet-abonnees. `services/quota.py` telt `story_generated`-events; over de
      limiet → **402** met `resets_at`. Abonnees (`active`/`in_grace`) onbeperkt.
- [x] App: paywall-CTA bij 402, "nog N deze week"-hint op home, echt
      paywall-scherm met live quota-banner (`GET /me/subscription`).
- [x] `POST /webhooks/revenuecat` — event-mapping + auth-check klaar; activeer
      met `REVENUECAT_WEBHOOK_AUTH` in `.env`.
- [ ] **Nog doen bij store-setup**: `purchases_flutter` (RevenueCat SDK) in de
      app (init met `appUserID = users.id`), App Store/Play producten,
      `REVENUECAT_WEBHOOK_AUTH`. Koop-knop toont nu "Binnenkort beschikbaar".

## Status — Fase 6 (polish & store-ready) ◑

- [x] **UI-polish**: fonts gebundeld (Baloo2/Nunito in `assets/google_fonts/`,
      geen netwerk meer nodig), `DreamyLoader` (ademende maan + fonkelende
      sterren) i.p.v. spinner, haptische feedback, dark mode gecheckt.
- [x] **Branding**: app-icoon + native splash (`tool/make_icon.py` →
      `flutter_launcher_icons` / `flutter_native_splash`), display-naam
      "Verhaaltjesmaker" in Info.plist + AndroidManifest.
- [x] **Account verwijderen** in de app (Instellingen, achter de ouder-gate) →
      `DELETE /me` (cascade + audio-bestanden; ook Supabase-authgebruiker als
      `SUPABASE_SERVICE_KEY` is gezet).
- [x] **Compliance-docs**: `docs/privacy-policy.md`, `docs/store-compliance.md`,
      `docs/store-submission.md`.
- [x] **Adversariële tests**: `backend/tests/test_adversarial.py`.
- [ ] Handmatig: privacybeleid publiceren + `PRIVACY_POLICY_URL` invullen,
      store-screenshots, age-rating/Data-safety, productie-backend deployen,
      `flutter build ipa` / `appbundle` (Apple/Google accounts).

**MVP-functionaliteit is compleet (Fase 1–5).** Fase 6 rest = handmatige
store-stappen — zie `docs/store-submission.md`.

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
