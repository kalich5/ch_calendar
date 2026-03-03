"""Constants for CH School & Work Calendar."""

DOMAIN = "ch_calendar"
PLATFORMS = ["sensor", "calendar"]

CONF_CANTON = "canton"
CONF_BIRTHDAYS = "birthdays"
CONF_FAMILY_HOLIDAYS = "family_holidays"
CONF_REMINDER_DAYS = "reminder_days"
CONF_REMINDER_DAILY = "reminder_daily"

DEFAULT_REMINDER_DAYS = 7
DEFAULT_REMINDER_DAILY = True

# All 26 Swiss cantons
CANTONS = {
    "AG": "Aargau",
    "AI": "Appenzell Innerrhoden",
    "AR": "Appenzell Ausserrhoden",
    "BE": "Bern",
    "BL": "Basel-Landschaft",
    "BS": "Basel-Stadt",
    "FR": "Fribourg / Freiburg",
    "GE": "Geneva / Genève",
    "GL": "Glarus",
    "GR": "Graubünden / Grisons",
    "JU": "Jura",
    "LU": "Lucerne / Luzern",
    "NE": "Neuchâtel",
    "NW": "Nidwalden",
    "OW": "Obwalden",
    "SG": "St. Gallen",
    "SH": "Schaffhausen",
    "SO": "Solothurn",
    "SZ": "Schwyz",
    "TG": "Thurgau",
    "TI": "Ticino",
    "UR": "Uri",
    "VD": "Vaud",
    "VS": "Valais / Wallis",
    "ZG": "Zug",
    "ZH": "Zurich / Zürich",
}

# Canton holiday membership
# Value: set of canton codes, or string "ALL"
CANTON_HOLIDAYS = {
    "new_year":              "ALL",
    "national_day":          "ALL",
    "christmas":             "ALL",
    "ascension":             {"AG","AI","AR","BE","BL","BS","FR","GE","GL","GR","JU","LU","NE","NW","OW","SG","SH","SO","SZ","TG","TI","UR","VD","VS","ZG","ZH"},
    "good_friday":           {"AG","AR","BE","BL","BS","GE","GL","GR","JU","LU","NE","SG","SH","SO","TG","VD","ZG","ZH"},
    "easter_monday":         {"AG","AI","AR","BE","BL","BS","FR","GE","GL","GR","JU","LU","NE","NW","OW","SG","SH","SO","SZ","TG","TI","UR","VD","VS","ZG","ZH"},
    "whit_monday":           {"AG","AI","AR","BE","BL","BS","FR","GE","GL","GR","JU","LU","NE","NW","OW","SG","SH","SO","SZ","TG","TI","UR","VD","VS","ZG","ZH"},
    "boxing_day":            {"AG","AI","AR","BE","BL","BS","FR","GL","GR","LU","NW","OW","SG","SH","SZ","TG","TI","UR","VS","ZG","ZH"},
    "berchtoldstag":         {"BE","FR","GE","JU","NE","VD","VS"},
    "labor_day":             {"BS","FR","GE","JU","NE","SO","TI","VD"},
    "corpus_christi":        {"AG","AI","FR","GR","JU","LU","NW","OW","SO","SZ","TI","UR","VS","ZG"},
    "assumption":            {"AG","AI","FR","GR","JU","LU","NW","OW","SO","SZ","TI","UR","VS","ZG"},
    "all_saints":            {"AG","AI","FR","JU","LU","NW","OW","SZ","TI","UR","VS","ZG"},
    "immaculate_conception": {"AG","AI","FR","GR","LU","NW","OW","SZ","TI","UR","VS","ZG"},
    "restored_republic":     {"GE"},
    "geneva_fast":           {"GE"},
    "federal_fast":          {"VD"},
    "st_nicholas_flue":      {"OW"},
    "knabenschiessen":       {"ZH"},
}

HOLIDAY_NAMES = {
    "new_year":              "Neujahr / Nouvel An",
    "berchtoldstag":         "Berchtoldstag",
    "good_friday":           "Karfreitag / Vendredi Saint",
    "easter_monday":         "Ostermontag / Lundi de Pâques",
    "labor_day":             "Tag der Arbeit / Fête du travail",
    "ascension":             "Auffahrt / Ascension",
    "whit_monday":           "Pfingstmontag / Lundi de Pentecôte",
    "corpus_christi":        "Fronleichnam / Fête-Dieu",
    "national_day":          "Bundesfeiertag / Fête nationale",
    "assumption":            "Mariä Himmelfahrt / Assomption",
    "all_saints":            "Allerheiligen / Toussaint",
    "immaculate_conception": "Mariä Empfängnis / Immaculée Conception",
    "christmas":             "Weihnachten / Noël",
    "boxing_day":            "Stephanstag / Saint-Étienne",
    "restored_republic":     "Restauration de la République",
    "geneva_fast":           "Jeûne genevois",
    "federal_fast":          "Lundi du Jeûne fédéral",
    "st_nicholas_flue":      "Bruder-Klaus-Tag",
    "knabenschiessen":       "Knabenschiessen (Zürich)",
}

# School holidays per canton
# Format: list of (name, (month_start, day_start), (month_end, day_end))
# For Easter-relative holidays use special keys handled in holidays.py
# These are approximate typical dates – the integration uses dynamic calculation
# for Easter-based holidays and fixed windows for fixed holidays.
# Summer holidays are defined per canton; others are calculated dynamically.

SCHOOL_HOLIDAY_NAMES = {
    "summer":    "Sommerferien / Vacances d'été",
    "autumn":    "Herbstferien / Vacances d'automne",
    "christmas": "Weihnachtsferien / Vacances de Noël",
    "sports":    "Sportferien / Vacances de sports",
    "spring":    "Frühlingsferien / Vacances de printemps",
}
