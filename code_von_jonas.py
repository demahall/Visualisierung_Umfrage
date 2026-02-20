#%%
from pathlib import Path
import pandas as pd
from src.plotting.plotting_config import apply_style, PALETTE
from typing import List
import matplotlib.pyplot as plt
import numpy as np
apply_style()

def likert_bar_plt(labels, x1, x2, lab1="KMU", lab2="GU", xlim=(1, 5), title=None):
    y = np.arange(len(labels))
    h = 0.35

    fig, ax = plt.subplots(figsize=(11, 0.45*len(labels) + 2))

    b1 = ax.barh(y - h/2, x1, h, color=PALETTE[0], label=lab1)
    b2 = ax.barh(y + h/2, x2, h, color=PALETTE[1], label=lab2)

    ax.set(yticks=y, yticklabels=labels, xlim=xlim, title=title)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="-", alpha=0.7)

    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_width() + 0.03, b.get_y() + b.get_height()/2,
                    f"{b.get_width():.1f}".replace(".", ","), va="center")

    ax.legend()
    plt.tight_layout()
    return fig, ax

def likert_means(df, cols, scale_map, missing="KeineAntwort"):
    nums = (df[cols]
           .replace(missing, np.nan)   # treat as missing
           .replace(scale_map)         # mapping
           .astype(float))
    means = nums.mean(axis=0, skipna=True).to_numpy()
    n_eff = nums.notna().sum(axis=0).to_numpy()  # answers per item (excluding KeineAntwort)
    return means, n_eff

# %% Load the dataframe (Use exportsetting: "Fragenb exportieren als: Fragencode" and "Antworten exportieren als Vollständige Antworten" )
survey_df = pd.read_excel('new_result_survey.xlsx')
survey_df = survey_df.set_index('Antwort ID')
survey_df = survey_df.replace("\xa0", " ", regex=True) # Unsichtbare Leerzeichen (\ax0) Ersetzen
print(survey_df.head)


# %% Apply general filtering
sur_df_flt = survey_df.loc[
    (survey_df["lastpage"] == 12) &
    (
    (survey_df["A1"] == "Produzierendes Unternehmen") |
    (survey_df["A1"] == "IT-/Entwicklungsdienstleister") |
    (survey_df["A1[other]"] == 'Ingenieurbüro') |
    (survey_df["A1[other]"] == 'Sondermaschinenbau + Service') |
    (survey_df["A1[other]"] == 'Sensortechnik-Unternehmen') )
    ].copy()

n_flt = sur_df_flt.shape[0]
print(f'The Dataset contains n = {n_flt} entries with the current filtering.')


# %% Filter for KMU and GU

sur_df_kmu = sur_df_flt.loc[
    (survey_df["A2"] != "> 250") |          # Warning !!! Entered an 'or'. In KMU definition its actually an 'and'
    ((survey_df["A3"] == "< 5 Mio. EUR") |
     (survey_df["A3"] == "5 - 50 Mio. EUR"))
    ].copy()
n_kmu = sur_df_kmu.shape[0]
print(f'The Dataset contains n = {n_kmu} KMU.')

sur_df_gu = sur_df_flt.loc[
    (survey_df["A2"] == "> 250") &
    ((survey_df["A3"] == "50 – 250 Mio. EUR") |
     (survey_df["A3"] == "> 250 Mio. EUR"))
    ].copy()
n_gu = sur_df_gu.shape[0]
print(f'The Dataset contains n = {n_gu} GU.')
if n_kmu + n_gu != n_flt : print(f'Warning!:  n_kmu + n_gu != n_flt')



# %% Frage C25
#    -> Welche der nachfolgenden Nutzenpotenziale erachten Sie als entscheidenden Motivator zur Umsetzung zirkulärer Wertschöpfungsprozesse?
#    -> Mapping Nicht entscheidend - Sehr sehr entschiedned auf 1-5 -> mittelwertbildung
scale_map = {
    "Nichtentscheidend": 1,
    "Geringentscheidend": 2,
    "Teilsentscheidend": 3,
    "Eherentscheidend": 4,
    "Sehrentscheidend": 5,
}
labels = [
    "Verbesserte Kunden- und Lieferantenbeziehung",
    "Entwicklung neuer Geschäftsmodelle\n(durch Erschließung neuer Märkte)",
    "Optimierung der Preisgestaltung\ndes Endprodukts",
    "Verbesserte Außendarstellung\ngegenüber dem Kunden",
    "Verbesserte Attraktivität des Unternehmens\nauf dem Arbeitsmarkt",
    "Reduktion von Materialkosten",
    "Gesetzgebung und rechtliche\nRahmenbedingungen",
    "Verbesserte Ökobilanz",
]

cols = [f"C25[{i}]" for i in range(1, 9)]

kmu_vals, kmu_n_eff = likert_means(sur_df_kmu, cols, scale_map)
gu_vals,  gu_n_eff  = likert_means(sur_df_gu,  cols, scale_map)
print(kmu_n_eff)
print(gu_n_eff)
fig, ax = likert_bar_plt(labels, kmu_vals, gu_vals,
                      lab1=f"KMU (n={n_kmu})", lab2=f"GU (n={n_gu})",
                      title="Nutzenpotenziale als Motivator zur Umsetzung zirkulärer Wertschöpfungsprozesse")
plt.show()




# %% Frage C27
#    -> Welche der nachfolgenden Industrie 4.0-Technologien generieren für Sie einen Mehrwert bei der Umsetzung zirkulärer Wertschöpfungsprozesse?
#    -> Mapping Nicht entscheidend - Sehr hoher mehrwert auf 1-5 -> mittelwertbildung
scale_map = {'Nichtentscheidend' : 1,
             'GeringerMehrwert'  : 2,
             'MittlererMehrwert' : 3,
             'HoherMehrwert'     : 4,
             'Sehr hoherMehrwert': 5}

labels = [
            "Traceability-Technologien\n(z. B. RFID, Barcode, QR-Code)",
            "Sensorik in Produkten\n(z. B. Druck, Drehzahl, Temperatur, …)",
            "Sensorik in Maschinen\n(z. B. Strom- oder Druckluftverbrauch, …)",
            "Standards zum Datenaustausch\n(z. B. OPC UA)",
            "Datenplattformen, Ökosysteme und Dateninfrastrukturen\n(z. B. Digitaler Produktpass)",
            "Künstliche Intelligenz und Datenanalyse\n(z. B. Zustandsüberwachung, datengetriebene Entscheidungsfindung, …)",
            "Simulationen\n(z. B. Materialflusssimulation)",
            "Verwaltungsschale\n(Asset Administration Shell, AAS)"
            ]

cols = [f"C27[{i}]" for i in range(1, 9)]

kmu_vals, kmu_n_eff = likert_means(sur_df_kmu, cols, scale_map)
gu_vals,  gu_n_eff  = likert_means(sur_df_gu,  cols, scale_map)
print(kmu_n_eff)
print(gu_n_eff)
fig, ax = likert_bar_plt(labels, kmu_vals, gu_vals,
                      lab1=f"KMU (n={n_kmu})", lab2=f"GU (n={n_gu})",
                      title="Generierter Mehrwert von Industrie 4.0-Technologien bei der Umsetzung zirkulärer Wertschöpfungsprozesse")
plt.show()



# %% Frage D30
#    -> In welchem Maß stellen die folgenden Punkte ein Hemmnis für die Umsetzung von Kreislaufwirtschaft in Ihrem Unternehmen dar?
#    -> Mapping kein hemmnis - hohes hemmnis 1-5 -> mittelwertbildung
scale_map = {
    "Kein Hemmnis": 1,  # Achtung ! Verstecktes/ Unsichtbares Leerzeichen (\xa0) wurde am anfang ersetzt
    "GeringesHemmnis": 2,
    "MittleresHemmnis": 3,
    "StarkesHemmnis": 4,
    "Sehr starkesHemmnis": 5,
}

labels = [
    "Fehlende Informationen zum Ressourcenbedarf\n(Material, Energie, …)",
    "Fehlende Informationen zu früher\nhergestellten Produkten\n(Materialien, Komponenten etc.)",
    "Daten aus der Lieferkette\n(Kunden, Lieferanten) nur schwer zugänglich",
    "Transportierbarkeit des Produkts\n(z. B. Abmaße, Gewicht)",
    "Niedrige Preise von Neuprodukten",
    "Schwierigkeiten zirkuläre Strategien\nökonomisch abzuwägen",
    "Schwierigkeiten zirkuläre Strategien\nökologisch abzuwägen",
    "Schwierigkeiten aus Strategien\nkonkrete Maßnahmen abzuleiten",
    "Geringe Unterstützung/Priorisierung\nder Unternehmensleitung",
    "Unklare Verantwortlichkeiten\nim Unternehmen",
    "Fehlende Kompetenzen zur Bewertung/\nBefundung zurückgeführter Produkte",
    "Fehlende Kompetenzen zur Demontage\nzurückgeführter Produkte",
    "Fehlende methodische Kompetenzen\nfür die Transformation\nzur Kreislaufwirtschaft",
    "Unklare gesetzliche\nRahmenbedingungen",
    "Geringe Vorbereitung auf\nanstehende Regelungen\n(z. B. PPWR, ESPR, Circular Economy Act)",
    "Zulassung, Zertifizierungen oder\nSicherheitsrelevanz von Produkten",
]

cols = [f"D30[{i}]" for i in range(1, 17)]

kmu_vals, kmu_n_eff = likert_means(sur_df_kmu, cols, scale_map)
gu_vals,  gu_n_eff  = likert_means(sur_df_gu,  cols, scale_map)
print(kmu_n_eff)
print(gu_n_eff)
fig, ax = likert_bar_plt(labels, kmu_vals, gu_vals,
                      lab1=f"KMU (n={n_kmu})", lab2=f"GU (n={n_gu})",
                      title="Hemmnis für die Umsetzung von Kreislaufwirtschaft in Unternehmen")
plt.show()




# %% Frage D31
#    -> Inwieweit stimmen Sie folgenden Aussagen zur Umsetzung von Kreislaufwirtschaft bezogen auf die Wettbewerbsfähigkeit aus der Sicht Ihres Unternehmens zu?
#    -> Mapping kein zustimmung - seh hohe zustimmung 1-5 -> mittelwertbildung
scale_map = {
    "KeineZustimmung": 1,
    "GeringeZustimmung": 2,
    "TeilweiseZustimmung": 3,
    "HoheZustimmung": 4,
    "Sehr hoheZustimmung": 5,
}

labels = [
    "Kreislauf-Anforderungen erhöhen Produktionskosten\nund führen zu sinkenden Margen",
    "Strengere EU-Vorgaben verschlechtern die Wettbewerbsposition\ngegenüber weniger regulierten Regionen",
    "KMU werden durch CE-Regulierung\nüberproportional belastet",
    "Zu restriktive CE-Vorgaben behindern\nInnovation und Produktvielfalt",
    "Regulatorische Unsicherheit und Dynamik in der EU\nführt zu Investitionszurückhaltung",
    "Steigende Nachfrage nach Recyclingmaterialien\nverursacht Engpässe und Preissteigerungen",
    "Recyclinggerechtes Design führt zu höheren Stückkosten\noder möglichen Qualitätseinbußen",
    "Rücknahme-, Recycling- und Nachweissysteme erhöhen\nden administrativen und logistischen Aufwand",
    "Verzögerte CE-Umsetzung führt zu Reputationsverlusten\nund schwächt die Marktstellung",
    "Nicht-Erfüllung von CE-Anforderungen gefährdet den Zugang\nzu nachhaltigen Lieferketten und Beschaffungsnetzwerken",
]

cols = [f"D31[{i}]" for i in range(1, 11)]

kmu_vals, kmu_n_eff = likert_means(sur_df_kmu, cols, scale_map)
gu_vals,  gu_n_eff  = likert_means(sur_df_gu,  cols, scale_map)
print(kmu_n_eff)
print(gu_n_eff)
fig, ax = likert_bar_plt(labels, kmu_vals, gu_vals,
                      lab1=f"KMU (n={n_kmu})", lab2=f"GU (n={n_gu})",
                      title="Umsetzung von Kreislaufwirtschaft bezogen auf die Wettbewerbsfähigkeit")
plt.show()


# %% Frage D32
#    -> In welchen Lebenszyklusphasen bzw. Elementen des zirkulären Wertschöpfungsprozesses sehen Sie die größten Hemmnisse für die Umsetzung zirkulärer Wertschöpfungsprozesse?
#    -> Mapping kein hemmnis - seh starkes hemmnis 1-5 -> mittelwertbildung
scale_map = {
    "KeinHemmnis": 1,
    "GeringesHemmnis": 2,
    "MittleresHemmnis": 3,
    "StarkesHemmnis": 4,
    "Sehr starkesHemmnis": 5,
}

labels = [
    "Produktdesign für R-Strategien",
    "Rückwärtslogistik",
    "Demontage",
    "Befundung",
    "Aufbereitung und Verwertung",
    "Remontage",
    "Endprüfung",
    "Geschäftsmodelle",
    "Definition geeigneter\nKennzahlen",
]

cols = [f"D32[{i}]" for i in range(1, 10)]

kmu_vals, kmu_n_eff = likert_means(sur_df_kmu, cols, scale_map)
gu_vals,  gu_n_eff  = likert_means(sur_df_gu,  cols, scale_map)
print(kmu_n_eff)
print(gu_n_eff)
fig, ax = likert_bar_plt(labels, kmu_vals, gu_vals,
                      lab1=f"KMU (n={n_kmu})", lab2=f"GU (n={n_gu})",
                      title="Hemmnisse entlang der Lebenszyklusphasen zirkulärer Wertschöpfungsprozesse")
plt.show()

# %%
