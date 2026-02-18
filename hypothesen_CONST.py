import numpy as np

# --- Exakte question_text Strings aus deinem Export! ---
Q11 = "Wird in Ihrem Unternehmen Kreislaufwirtschaft bereits umgesetzt?"
Q2 = "Wie viele Beschäftigte hat Ihr Unternehmen?"
Q4 = "In welcher Branche ordnen Sie Ihre Tätigkeit ein?"
Q10 = "Wie ordnen Sie die monatliche Stückzahl Ihrer Fertigung ein?"

# --- Hemmnisse Blöcke
Q31 = "In welchem Maß stellen die folgenden Punkte ein Hemmnis für die Umsetzung von Kreislaufwirtschaft in Ihrem Unternehmen dar?"
Q32 = "Inwieweit stimmen Sie folgenden Aussagen zur Umsetzung von Kreislaufwirtschaft bezogen auf die Wettbewerbsfähigkeit aus der Sicht Ihres Unternehmens zu?"
Q33 = "In welchen Lebenszyklusphasen bzw. Elementen des zirkulären Wertschöpfungsprozesses sehen Sie die größten Hemmnisse für die Umsetzung zirkulärer Wertschöpfungsprozesse?"

# --- Likert mappings (H4) ---
LIKERT_HEMMNIS_MAPPING = {
    "Kein Hemmnis": 1,
    "Geringes Hemmnis": 2,
    "Mittleres Hemmnis": 3,
    "Starkes Hemmnis": 4,
    "Sehr starkes Hemmnis": 5,
    "Keine Antwort": np.nan,
}

LIKERT_ZUSTIMMUNG_MAPPING = {
    "Keine Zustimmung": 1,
    "Geringe Zustimmung": 2,
    "Teilweise Zustimmung": 3,
    "Hohe Zustimmung": 4,
    "Sehr hohe Zustimmung": 5,
    "Keine Antwort": np.nan,
}


# H2: Material-cost grouping + sorting + marking

HIGH_COST_INDUSTRIES = {
    "Maschinenbau",
    "Metallerzeugung und -bearbeitung",
    "Fahrzeugbau",
    "Luft- und Raumfahrttechnik",
    "Elektrische Geräte und Komponenten",
    "Reparatur und Installation von Maschinen und Ausrüstungen",
}
LOW_COST_INDUSTRIES = {
    "Nahrungs- und Futtermittel",
    "Getränkeherstellung oder -abfüllung",
    "Textilien, Leder, Lederwaren oder Schuhe",
    "Herstellung von Möbeln",
    "Druckerzeugnisse",
    "Papierbranche",
}

#H4: Kategorisierung der Hemmnisse

STRONG_CATEGORY_HEMMNIS = {"Starkes Hemmnis", "Sehr starkes Hemmnis"}
STRONG_CATEGORY_ZUSTIMMUNG = {"Hohe Zustimmung ", "Sehr hohe Zustimmung"}


JA_NEIN_MAPPING = {"Ja": 1, "Nein": 0}