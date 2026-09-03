# Store-compliance — kids-categorie (Fase 6 stap 18)

Checklist voor Apple's **Kids Category** en Google Play's **Families**-programma,
afgezet tegen wat de app doet. ✅ = geregeld, ⚠️ = actie nodig.

## Apple — Kids Category / App Review Guideline 1.3 & 5.1.4

| Eis | Status | Toelichting |
|---|---|---|
| Geen advertenties van derden (of alleen COPPA-conforme, contextuele) | ✅ | Geen ads in de app. |
| Geen third-party analytics/tracking zonder toestemming | ✅ | Geen analytics-SDK's. Backend logt alleen technisch (geen kind-PII). |
| Geen verzamelen van persoonsgegevens van kinderen | ✅ | Alleen ouder-e-mail. Kind heeft geen account, geen naam/leeftijd/locatie. |
| Ouder-gate vóór externe links, aankopen en "about"-info | ✅ | `/settings` en `/paywall` zitten achter de rekensom-gate (`Routes.gated`). Geen andere uitgaande links in de app. |
| Links naar buiten de app achter ouder-gate | ✅ | Privacybeleid-link (toe te voegen in Instellingen) moet achter de gate of als niet-klikbare tekst — nu staat Instellingen al achter de gate. |
| Privacybeleid-URL in de listing én in de app | ⚠️ | `docs/privacy-policy.md` publiceren op een vaste URL; URL invullen in App Store Connect en in het instellingenscherm. |
| Leeftijdsclassificatie correct | ⚠️ | Zet **4+** (geen ongepaste content; moderatie dwingt dit af). Vul de "Age Rating"-vragenlijst eerlijk in (geen geweld, geen volwassen thema's). |
| Privacy "nutrition labels" (App Privacy) | ⚠️ | Aangeven: "Contact Info → Email Address", "User Content → Other User Content (verhaaltjes)", gekoppeld aan identiteit, **niet** gebruikt voor tracking. |
| Account-verwijdering in de app of duidelijk vindbaar | ⚠️ | Apple vereist in-app account-verwijdering of een directe route ernaartoe. Nu: mail naar support (staat in privacybeleid). **Aanrader:** een "Account verwijderen"-knop in Instellingen (achter de gate) toevoegen. |
| Geen gedrags-/psychologische manipulatie richting kind om te kopen | ✅ | Paywall zit achter de ouder-gate; kind ziet alleen "op maandag weer 2 gratis". |

## Google Play — Families Policy / Designed for Families

| Eis | Status | Toelichting |
|---|---|---|
| Target audience & content-instelling correct in Play Console | ⚠️ | Kies "Kinderen en volwassenen" of "Alleen kinderen" bewust; vul de Families-vragenlijst in. |
| Data safety-formulier | ⚠️ | Zelfde gegevens als Apple: e-mail (account), user content (verhaaltjes), geen tracking, versleuteld in transit, verwijdering op verzoek. |
| Geen ads / alleen gecertificeerde ad-SDK's voor Families | ✅ | Geen ads. |
| APIs voor kinderen niet gebruiken op onveilige manier (bv. geen AdID) | ✅ | Geen advertising ID, geen device fingerprinting. |
| Privacybeleid-URL | ⚠️ | Zelfde URL als Apple. |
| Inhoud geschikt voor de gekozen leeftijdsgroep | ✅ | Moderatie-laag (blocklist + Claude-classifier, faalt gesloten) borgt dit; onderwerpen zijn een vaste, veilige catalogus. |

## AVG / GDPR-K (EU)

| Eis | Status | Toelichting |
|---|---|---|
| Rechtsgrond voor verwerking ouder-e-mail | ✅ | Uitvoering van de overeenkomst (account + bewaren). |
| Geen profilering van kinderen | ✅ | Niet gedaan. |
| Recht op inzage / verwijdering | ✅ (proces) | In-app verwijderen van verhaaltjes; account-verwijdering via support. Zie ⚠️ hierboven voor in-app knop. |
| Verwerkersovereenkomsten met subverwerkers | ⚠️ | DPA's regelen/bevestigen met Supabase, Anthropic, RevenueCat. |
| Verwerkingsverantwoordelijke identificeerbaar | ⚠️ | Naam/bedrijf invullen in het privacybeleid. |

## Techniek die de compliance ondersteunt (al aanwezig)

- Ouder-gate: `app/lib/src/core/parental_gate/` — 5 min geldig, niet gepersisteerd.
- Moderatie: `backend/app/services/{prompts,blocklist,moderation}.py` — faalt gesloten.
- Autorisatie: `_get_owned_story` (IDOR → 404).
- Geen tracking/ads-code in de codebase.
- Prod-defaults: geen `/docs`, geen SQL-echo, HTTPS afgedwongen door iOS ATS.

## Openstaande acties (samengevat)

1. Privacybeleid publiceren op vaste URL + invullen: verantwoordelijke, (post)adres.
2. URL toevoegen in App Store Connect, Play Console én in het app-instellingenscherm.
3. **"Account verwijderen"-knop** in Instellingen (achter de gate) — sterk aanbevolen voor Apple.
4. Age rating 4+ / Families-vragenlijsten invullen.
5. App Privacy labels / Data safety-formulier invullen (e-mail + user content, geen tracking).
6. DPA's met Supabase / Anthropic / RevenueCat bevestigen.
