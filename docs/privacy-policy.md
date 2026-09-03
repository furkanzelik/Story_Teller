# Privacybeleid — Verhaaltjesmaker

_Laatst bijgewerkt: 2026-09-03_

Verhaaltjesmaker ("de app") is een app waarmee ouders samen met hun kind korte,
AI-gegenereerde bedtijdverhaaltjes maken en laten voorlezen. Dit beleid legt uit
welke gegevens we verwerken en waarom. We houden het bewust minimaal.

## Korte samenvatting

- **Geen advertenties.** Geen advertentienetwerken, geen tracking van kinderen.
- **Geen analytics van derden** die individuele gebruikers volgt.
- **Geen verkoop of delen** van persoonsgegevens.
- We verwerken alleen een **ouder-account (e-mailadres)** en de **verhaaltjes**
  die in de app worden gemaakt.
- De app is bedoeld om door een volwassene te worden ingesteld en beheerd.

## Welke gegevens we verwerken

| Gegeven | Waarom | Bewaartermijn |
|---|---|---|
| E-mailadres van de ouder | Inloggen (eenmalige code per e-mail) en het account koppelen aan bewaarde verhaaltjes | Tot het account wordt verwijderd |
| Inlog-tokens (technisch) | Beveiligde toegang tot de app | Kort; automatisch vernieuwd/verlopen |
| Gemaakte verhaaltjes (titel, tekst, gekozen onderwerp, leeftijdsgroep) | Tonen in de app en, als je erop tikt, bewaren in "Mijn verhaaltjes" | Niet-bewaarde verhaaltjes: tijdelijk. Bewaarde verhaaltjes: tot je ze verwijdert of het account opzegt |
| Voorlees-audio (gegenereerd geluidsbestand) | Het verhaaltje kunnen voorlezen | Gekoppeld aan het verhaaltje; verwijderd met het verhaaltje |
| Gebruiksteller (aantal verhaaltjes per week) | De gratis-limiet en, bij een abonnement, de facturering afhandelen | Rollend; oude records vervallen |

We vragen **niet** om de naam, leeftijd, foto, locatie of het apparaat-ID van
het kind. Het kind hoeft geen eigen account te hebben.

## Kinderen

De app is ontworpen voor gezinnen. Alleen een volwassene maakt een account aan en
beheert instellingen en betalingen; die schermen zitten achter een **ouder-slot**
(een rekensom). We verzamelen niet bewust persoonsgegevens van kinderen onder de
16 jaar. Als je denkt dat een kind ons zonder toestemming gegevens heeft gegeven,
mail dan furkanzelik@gmail.com en we verwijderen het.

## Wie de gegevens verwerkt (subverwerkers)

- **Supabase** — accounts/inloggen en database (hosting in de EU indien
  ingesteld). Zie supabase.com/privacy.
- **Anthropic (Claude)** — genereert de verhaaltekst en voert de
  inhoudscontrole uit. Er wordt alleen een gekozen onderwerp + leeftijdsgroep
  gestuurd; geen accountgegevens. Zie anthropic.com/legal/privacy.
- **RevenueCat** — alleen als je een abonnement neemt: verwerkt de
  abonnementsstatus (geen betaalgegevens; die blijven bij Apple/Google). Zie
  revenuecat.com/privacy.

De voorlees-audio wordt lokaal/serverzijdig gegenereerd; er gaat geen
verhaaltekst naar een externe spraakdienst tenzij dit later expliciet wordt
toegevoegd en hier wordt vermeld.

## Betalingen

Abonnementen lopen via de App Store (Apple) of Google Play. Wij ontvangen geen
kaartgegevens; we ontvangen alleen of een abonnement actief is.

## Jouw rechten

Je kunt op elk moment:

- je bewaarde verhaaltjes inzien en verwijderen in de app;
- je account en alle bijbehorende gegevens laten verwijderen door te mailen naar
  **furkanzelik@gmail.com** (verwerkt binnen 30 dagen);
- een kopie van je gegevens opvragen.

## Beveiliging

Verbindingen verlopen versleuteld (HTTPS). Toegang tot verhaaltjes is beperkt tot
het eigen account. Zie ook `docs/` voor de technische beveiligingsmaatregelen.

## Wijzigingen

Bij belangrijke wijzigingen passen we de datum bovenaan aan en, waar nodig,
informeren we je in de app.

## Contact

**furkanzelik@gmail.com**

---

> **In te vullen vóór publicatie:** naam van de verantwoordelijke
> (persoon/bedrijf) en, indien van toepassing, een postadres — de meeste stores
> en de AVG vereisen een identificeerbare verwerkingsverantwoordelijke. Publiceer
> dit document op een vaste openbare URL en zet die URL in de App Store /
> Play Console listing én in het instellingenscherm van de app.
