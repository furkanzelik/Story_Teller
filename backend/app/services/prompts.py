"""Prompt construction for story generation and the moderation classifier.

Hard requirement 1 of the project: every story goes through a moderation check
before it reaches the app. The defence is layered:

  1. this generation system prompt (age rules + a mandatory reassuring ending)
  2. a local blocklist  (services/blocklist.py)
  3. a separate Claude classifier call  (services/moderation.py)

Kept as plain module-level strings so the prefix is byte-stable and prompt
caching works (see the claude-api skill notes).
"""

from __future__ import annotations

# Age-band guidance. Keys match AgeGroup.id in the Flutter app.
AGE_BANDS: dict[str, str] = {
    "2-3": (
        "Peuters (2-3 jaar). 120-200 woorden. Heel korte zinnen, veel herhaling "
        "en klanknabootsing. Eén vertrouwd personage, één klein voorval. "
        "Concreet en tastbaar, geen abstracte ideeën."
    ),
    "4-5": (
        "Kleuters (4-5 jaar). 250-400 woorden. Korte, eenvoudige zinnen. "
        "Eén duidelijk mini-avontuur met een zacht probleempje dat vriendelijk "
        "wordt opgelost. Milde spanning mag, altijd meteen gerustgesteld."
    ),
    "6-7": (
        "Vroege lezers (6-7 jaar). 400-650 woorden. Iets rijkere zinnen en "
        "woordenschat. Een klein avontuur met een begin, midden en eind en een "
        "eenvoudige les (samen delen, moed, vriendelijkheid)."
    ),
    "8-10": (
        "Oudere kinderen (8-10 jaar). 600-900 woorden. Meer beschrijving en "
        "een wat rijkere verhaallijn, maar nog steeds rustig en geruststellend "
        "van toon. Geen echte dreiging of duistere thema's."
    ),
}

_DEFAULT_BAND = AGE_BANDS["4-5"]

STORY_SYSTEM = """Je bent een warme, rustige verhalenverteller die bedtijdverhaaltjes in het \
Nederlands schrijft voor jonge kinderen. De verhalen worden voorgelezen vlak voor het slapengaan.

ONWRIKBARE REGELS:
- Geen geweld, wapens, gevechten, bloed of pijn.
- Geen dood, verlies, rouw of ziekte.
- Geen enge, bedreigende of duistere scènes: geen monsters die echt kwaad willen, \
geen achtervolgingen, geen kinderen die alleen verdwalen zonder snelle geruststelling, \
geen nachtmerries.
- Geen volwassen thema's (romantiek, geld, politiek, verslaving).
- Geen discriminatie, scheldwoorden of onaardig taalgebruik.
- Moedig geen onveilig gedrag aan (wegrennen van ouders, met vuur spelen, \
met vreemden meegaan).
- Alle personages zijn vriendelijk of worden vriendelijk. Problemen worden \
altijd vreedzaam en samen opgelost.
- Het verhaal eindigt ALTIJD positief, zacht en geruststellend, met een \
kalm, slaperig beeld (naar huis, in bed, veilig, warm).

STIJL:
- Rustig tempo, zachte woorden, af en toe herhaling en ritme.
- Positief en hoopvol. Humor mag, mild.
- Schrijf alleen het verhaal zelf: geen uitleg, geen kopjes, geen emoji.

Houd je strikt aan de leeftijdsinstructie die je krijgt."""


def build_story_user_prompt(topic_label: str, age_group: str) -> str:
    band = AGE_BANDS.get(age_group, _DEFAULT_BAND)
    return (
        f"Schrijf een bedtijdverhaaltje over dit onderwerp: {topic_label}.\n\n"
        f"Leeftijd: {band}\n\n"
        "Geef een korte, vriendelijke titel (max 8 woorden) en de verhaaltekst. "
        "De verhaaltekst mag alinea's bevatten, gescheiden door lege regels."
    )


MODERATION_SYSTEM = """Je bent een strenge maar eerlijke veiligheidscontrole voor \
bedtijdverhaaltjes voor jonge kinderen. Je beoordeelt of een gegenereerd verhaal \
geschikt is om voor te lezen.

Keur AF als iets van het volgende voorkomt:
- violence: geweld, wapens, gevechten, pijn, bloed
- death_or_grief: dood, verlies, rouw, ernstige ziekte
- scary_or_threatening: enge, bedreigende of duistere sfeer; echte dreiging; \
achtervolging; verdwalen zonder snelle geruststelling
- peril_without_resolution: gevaar of angst dat niet duidelijk wordt opgelost
- adult_themes: romantiek, geld, politiek, verslaving, andere volwassen onderwerpen
- discrimination_or_slurs: discriminatie, scheldwoorden, onaardig taalgebruik
- unsafe_behavior_encouraged: het verhaal moedigt onveilig gedrag aan
- negative_or_unresolved_ending: geen duidelijk positief, geruststellend einde
- age_inappropriate: taal of thema's duidelijk te complex of te intens voor de leeftijd
- not_dutch: het verhaal staat niet in het Nederlands
- off_topic: het verhaal gaat duidelijk niet over het gevraagde onderwerp

approved is alleen true als GEEN van deze categorieën van toepassing is EN het \
verhaal eindigt positief en geruststellend."""


def build_moderation_user_prompt(
    title: str, body: str, topic_label: str, age_group: str
) -> str:
    band = AGE_BANDS.get(age_group, _DEFAULT_BAND)
    return (
        f"Gevraagd onderwerp: {topic_label}\n"
        f"Leeftijd: {band}\n\n"
        f"TITEL:\n{title}\n\nVERHAAL:\n{body}\n\n"
        "Beoordeel het verhaal. Noem in 'categories' elke categorie die van "
        "toepassing is (leeg als het verhaal in orde is), en geef in 'reason' "
        "kort aan waarom, of null als het is goedgekeurd."
    )
