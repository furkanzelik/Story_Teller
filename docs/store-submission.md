# Store-submissie — voorbereiding (Fase 6 stap 20)

Checklist om Verhaaltjesmaker naar de App Store en Google Play te brengen.
Zie ook `store-compliance.md` (kids-categorie) en `privacy-policy.md`.

## 0. Accounts & basis

- [ ] Apple Developer Program ($99/jaar) — nodig voor signing en submissie.
- [ ] Google Play Console (eenmalig $25).
- [ ] Bundle-/package-ID definitief: `com.storyteller.storyTellerApp`
      (in `ios/Runner.xcodeproj` en `android/app/build.gradle`). Wijzigen kan nu
      nog; na de eerste release niet meer.
- [ ] Versie: `pubspec.yaml` → `version: 1.0.0+1` (naam+build). Verhoog `+1` per
      upload.

## 1. Assets (grotendeels gegenereerd)

- [x] App-icoon — `assets/branding/icon.png` → `dart run flutter_launcher_icons`.
- [x] Splash — `assets/branding/splash_logo.png` → `dart run flutter_native_splash:create`.
- [x] Display-naam "Verhaaltjesmaker" in `Info.plist` en `AndroidManifest.xml`.
- [ ] **Screenshots** per vereist formaat (iPhone 6.7"/6.5", iPad; Android phone/tablet).
      Maak ze van: home, onderwerp-keuze, verhaal + audiospeler, bibliotheek, paywall.
- [ ] App Store: promo-tekst, beschrijving, keywords, support-URL, marketing-URL (optioneel).
- [ ] Play: korte + volledige beschrijving, feature graphic (1024×500).

## 2. Iconentweak (optioneel)

Het huidige icoon (maan + sterren, indigo verloop) is functioneel. Voor een
strakker resultaat: bewerk `tool/make_icon.py` of vervang `assets/branding/*.png`
door een ontwerp van een designer en draai de twee generate-commando's opnieuw.

## 3. Compliance-invoer (uit `store-compliance.md`)

- [ ] Privacybeleid publiceren op een vaste URL; die URL zetten in:
      App Store Connect · Play Console · `assets/.env` → `PRIVACY_POLICY_URL`
      (dan wordt de "Privacybeleid"-tegel in Instellingen klikbaar).
- [ ] Leeftijdsclassificatie **4+** / Play-contentbeoordeling invullen.
- [ ] App Privacy (Apple) / Data safety (Google): e-mailadres (account) +
      user content (verhaaltjes), gekoppeld aan identiteit, **geen tracking**.
- [ ] Kids/Families-programma aanvragen indien gewenst (of gewoon 4+ zonder
      Families — dan minder eisen, maar ook minder zichtbaarheid in kid-secties).
- [x] In-app account-verwijdering — aanwezig (Instellingen → "Account verwijderen",
      achter de ouder-gate; backend `DELETE /me`).

## 4. Productie-backend (vóór submissie live)

- [ ] Backend deployen met **HTTPS** (bijv. Fly.io / Render / eigen VPS + Caddy).
- [ ] `backend/.env` productie: **geen** `ENVIRONMENT`/`DEBUG` (defaults =
      production, geen `/docs`, geen SQL-echo). `ANTHROPIC_API_KEY`,
      `SUPABASE_URL`, `CORS_ORIGINS` zetten. Optioneel `REVENUECAT_WEBHOOK_AUTH`,
      `SUPABASE_SERVICE_KEY` (voor volledige account-verwijdering).
- [ ] `alembic upgrade head` op de productie-database.
- [ ] Piper-stem meeleveren of TTS_PROVIDER wisselen naar een cloud-stem.
- [ ] Object-storage voor audio i.p.v. lokale schijf (zie `services/storage.py`);
      audio achter auth of signed URL zetten (openstaand security-punt).
- [ ] Opschoontaak: niet-bewaarde verhalen + wees-audio ouder dan 7 dagen.
- [ ] `app/assets/.env` (release): `API_BASE_URL=https://…`, `DEBUG_LOGGING=false`.

## 5. Builds

```bash
# iOS (heeft Apple Developer-account + signing nodig)
cd app && flutter build ipa --release
# -> app/build/ios/ipa/*.ipa  → uploaden via Transporter of Xcode Organizer

# Android
cd app && flutter build appbundle --release
# -> app/build/app/outputs/bundle/release/app-release.aab
# Eerst een upload-keystore aanmaken en android/key.properties instellen.
```

## 6. Fase 5 afmaken bij store-setup

- [ ] `purchases_flutter` (RevenueCat) toevoegen; SDK init met `appUserID = users.id`.
      `StubPurchasesService` in `subscription_controller.dart` vervangen door de
      echte implementatie; de koop-knop op de paywall activeert dan vanzelf.
- [ ] Abonnement-producten in App Store Connect / Play Console.
- [ ] `REVENUECAT_WEBHOOK_AUTH` in de productie-`.env`.

## 7. Laatste check

- [ ] `flutter test` + `pytest` groen.
- [ ] Handmatige doorloop op een echt toestel: login, verhaal, audio, opslaan,
      bibliotheek, limiet → paywall, ouder-gate, account verwijderen.
- [ ] Adversariële onderwerpen geprobeerd (zie `backend/tests/test_adversarial.py`).
