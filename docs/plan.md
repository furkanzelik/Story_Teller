# Stappenplan

## Fase 1 — Fundament
1. Flutter project opzetten (structuur, navigatie, state management — Riverpod)  ✅
2. Backend skeleton (FastAPI), lokaal draaiend                                    ✅
3. PostgreSQL schema: users, stories, topics, subscriptions (+ usage_events)     ✅
4. Auth opzetten (Supabase) — ouder-account, geen los kind-account               ✅

## Fase 2 — Kernfunctionaliteit (het verhaal)
5. Topic-selectiescherm in Flutter (tegels/lijst, later vrij tekstveld)      ✅ (Fase 1)
6. Backend: topic + leeftijd → prompt → Claude-call → ruwe tekst             ✅
7. Moderatie-laag: blocklist + Claude-classifier, faalt gesloten            ✅
8. Verhaalscherm: laadstatus, tekst tonen, "opnieuw genereren"              ✅

LLM: Claude Haiku 4.5 (`claude-haiku-4-5`) voor generatie én moderatie.
Flow: `POST /stories/generate` → genereer → modereer → bij afkeuring 1× opnieuw
→ anders 422 (met `rejected`-rij voor audit). Goedgekeurd verhaal wordt
`approved` opgeslagen + `usage_event`.

## Fase 3 — Audio ✅
9.  TTS-provider: **Piper** (open-source, offline, gratis, stem `nl_NL-pim-medium`)  ✅
10. `POST /stories/{id}/audio` → synth → mp3 cachen in `backend/media/`, serven via `/media`  ✅
11. Audiospeler in Flutter (`just_audio`): play/pause, voortgangsbalk, auto-laden  ✅

Provider-onafhankelijk (`services/tts.py`): `TTS_PROVIDER=elevenlabs` + key omzetten
en de rest verandert niet. Piper-synth ~30-40s voor een heel verhaal (draait
ná de tekst, wordt gecacht); ElevenLabs/Google zou ~3-5s zijn.

## Fase 4 — Bewaren & gebruikers ✅
12. "Opslaan": `PUT /stories/{id}/saved`, hartje op verhaalscherm (optimistisch)  ✅
13. Bibliotheekscherm: `GET /stories` (alleen saved+approved, per user), tik → heropenen  ✅

Autorisatie centraal in `_get_owned_story` (IDOR → 404). `GET /stories/{id}` voor
heropenen. Rate limiting toegevoegd (`services/rate_limit.py`, via `usage_events`):
20 generaties + 40 audio per user per uur.

## Fase 5 — Monetization & compliance
14. Ouder-gate vóór instellingen en betaalscherm  (client-deel staat al)
15. Abonnementslaag via RevenueCat
16. Gratis-laag limiet (bv. 2 verhalen/week zonder abonnement) — via usage_events

## Fase 6 — Polish & store-ready
17. Kindvriendelijke UI-polish
18. Privacybeleid + kids-categorie eisen Apple/Google
19. Testen met echte topics/edge cases
20. Store-submissie

## Harde eisen (niet onderhandelbaar)
1. Moderatie-check op elke verhaaltekst vóór teruggeven.
2. Ouder-gate vóór instellingen en betaalscherm.
3. Geen tracking/advertenties gericht op kinderen.
4. Geen in-app aankopen die het kind zelf kan doen.

## Keuzes tot nu toe
- **State management:** Riverpod 2.6 (Notifier-API, geen codegen — minder
  buildtooling voor de MVP). Upgrade naar Riverpod 3 kan als de Flutter-
  constraints het toelaten.
- **Navigatie:** go_router — declaratief, `redirect` levert de route-guard voor
  de ouder-gate.
- **Backend:** FastAPI + SQLAlchemy 2.0 (typed) + Alembic. psycopg 3.
- **Auth (voorstel):** Supabase — auth + storage + Postgres in één, minder
  integratiewerk dan Firebase omdat we Postgres toch al draaien.
- **Topics:** vaste catalogus in de DB (`topics`), met een Flutter-fallbacklijst.
  Vrij tekstveld pas later en achter de ouder-gate (grootste moderatie-risico).
