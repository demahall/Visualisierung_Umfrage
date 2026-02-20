import numpy as np


# --- CONFIG: adjust to your exact column names in df_tidy ---
COL_ID = "respondent_id"

# --- Allgemeine Frage, die zur Hypothesen verwendet werden! ---
Q2 = "Wie viele Beschäftigte hat Ihr Unternehmen?"
Q3 = "Wie hoch ist der jährliche Umsatz Ihres Unternehmens?"
Q10 = "Wie ordnen Sie die monatliche Stückzahl Ihrer Fertigung ein?"

Q11 = "Wird in Ihrem Unternehmen Kreislaufwirtschaft bereits umgesetzt?"
Q4 = "In welcher Branche ordnen Sie Ihre Tätigkeit ein?"
Q10 = "Wie ordnen Sie die monatliche Stückzahl Ihrer Fertigung ein?"
Q13 = "Welche der nachfolgend aufgeführten Punkte sind für Ihr Unternehmen zutreffend?"
Q16 = "Bitte bewerten Sie, inwieweit Daten in Ihrem Unernehmen erfasst und genutzt werden."
Q17 = "Welche der nachfolgenden Industrie 4.0 - Technologien werden derzeit in Ihrem Unternehmen eingesetzt und welche sind zukünftig in Planung?"

#
Q20 = "Stimmen Sie nachfolgenden Aussagen zur Digitalisierung und Quantifizierung zirkulärer Wertschöpfungsprozesse zu?"
ITEM_Q20_1= "In unserem Unternehmen ist die Kennzahlenstruktur (Kaskade) für lineare Produktionsprozesse klar definiert und mit den strategischen Zielen verknüpft."

ITEM_Q20_2 = "Für zirkuläre Prozesse (z.B. Rückführung, Aufbereitung, Remanufacturing) existieren vergleichbare Kennzahlensysteme."


# --- Hemmnisse Blöcke
Q18 = "Bitte bewerten Sie, inwieweit Daten in Ihrem Unernehmen erfasst und genutzt werden."
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

LIKERT_Q16_MAPPING = {
    "Keine Erfassung": 1,
    "Manuelle Erfassung, keine Nutzung": 2,
    "Manuelle Erfassung, manuelle Auswertung": 3,
    "Automatisierte Erfassung, manuelle Auswertung": 4,
    "Automatisierte Erfassung, automatisierte Auswertung": 5,
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

#Valid answer list
VALID_ANSWERS_Q17 = ["Im Einsatz", "In Planung"]
VALID_ANSWERS_YN = ["Ja", "Nein"]
