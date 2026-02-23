import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO
import textwrap


df = pd.read_csv("df_tidy.csv", names=["respondent_id","question_text","item","answer"], header=None)


# -----------------------------
# 1) Helpers to build respondent-level table
# -----------------------------

def get_single_choice(df: pd.DataFrame, qtext: str) -> pd.Series:

    """
    Returns a Series indexed by respondent_id with the (single) answer.
    If there are multiple answers per respondent, it keeps the first.
    """

    sub = df[df["question_text"] == qtext].copy()
    sub = sub.sort_values(["respondent_id"])
    # answers appear in 'answer' column; item is usually empty
    s = sub.groupby("respondent_id")["answer"].first()
    return s

def get_multi_choice_rows(df: pd.DataFrame, qtext: str) -> pd.DataFrame:
    """
    Returns rows for a multi-select question. Each row = respondent_id selected 'answer' option.
    In your data, multi-select answers are also stored in 'answer' (item empty).
    """
    sub = df[df["question_text"] == qtext].copy()
    return sub[["respondent_id", "answer"]].rename(columns={"answer": "option"})

def ce_binary_from_q11(ce_series: pd.Series) -> pd.Series:
    m = {"Ja": 1, "Nein": 0, "yes": 1, "no": 0}
    out = ce_series.map(lambda x: m.get(str(x).strip(), np.nan))
    return out.astype("float")

# -----------------------------
# 2) Diverging bar chart (left=No, right=Yes) in %
# -----------------------------

def diverging_yes_no_plot(summary: pd.DataFrame, group_col: str, title: str):
    """
    summary must have columns: group_col, n, yes, no, yes_pct, no_pct
    """
    s = summary.copy()
    s = s.sort_values("yes_pct", ascending=False)  # optional sorting
    y = np.arange(len(s))
    left = -s["no_pct"].values
    right = s["yes_pct"].values

    fig, ax = plt.subplots(figsize=(10, max(4, 0.45 * len(s))))
    ax.barh(y, left, label="noch nicht umgesetzt")
    ax.barh(y, right, label="bereits umgesetzt")

    ax.axvline(0, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{g} (n={int(n)})" for g, n in zip(s[group_col], s["n"])])
    ax.set_xlabel("Anteil der Teilnehmer in %")
    ax.set_title(title)

    # labels inside bars
    for i, (no_pct, yes_pct, no_n, yes_n) in enumerate(zip(s["no_pct"], s["yes_pct"], s["no"], s["yes"])):
        if no_pct > 0:
            ax.text(-no_pct/2, i, f"{no_pct:.0f}%\n({int(no_n)})", va="center", ha="center", fontsize=9)
        if yes_pct > 0:
            ax.text(yes_pct/2, i, f"{yes_pct:.0f}%\n({int(yes_n)})", va="center", ha="center", fontsize=9)

    ax.legend(loc="lower right")
    ax.set_xlim(-100, 100)
    plt.tight_layout()
    plt.show()

def summarize_yes_no_by_group(respondent_table: pd.DataFrame, group_col: str, ce_col: str = "CE"):
    sub = respondent_table.dropna(subset=[group_col, ce_col]).copy()
    g = sub.groupby(group_col)[ce_col]
    out = pd.DataFrame({
        group_col: g.size().index,
        "n": g.size().values,
        "yes": g.sum().values,
    })
    out["no"] = out["n"] - out["yes"]
    out["yes_pct"] = (out["yes"] / out["n"]) * 100
    out["no_pct"] = (out["no"] / out["n"]) * 100
    return out

# -----------------------------
# 3) H1 / H3 respondent-level tables (single-choice)
# -----------------------------

Q11_CE = "Wird in Ihrem Unternehmen Kreislaufwirtschaft bereits umgesetzt?"
Q10_SERIES = "Wie ordnen Sie die monatliche Stückzahl Ihrer Fertigung ein?"
Q2_EMPLOYEES = "Wie viele Beschäftigte hat Ihr Unternehmen?"  # change to exact text in your dataset

# Build respondent table with CE + series-size (H3)
resp = pd.DataFrame(index=sorted(df["respondent_id"].unique()))
resp.index.name = "respondent_id"
resp["CE"] = ce_binary_from_q11(get_single_choice(df, Q11_CE))
resp["series_size"] = get_single_choice(df, Q10_SERIES)

# H3 plot (works with your sample)
h3_summary = summarize_yes_no_by_group(resp.reset_index(), "series_size", "CE")
diverging_yes_no_plot(h3_summary, "series_size", "H3: Seriengröße (Q10) vs. CE umgesetzt (Q11)")

# H1 plot (only if your dataset contains the employee question)
if (df["question_text"] == Q2_EMPLOYEES).any():
    resp["firm_size"] = get_single_choice(df, Q2_EMPLOYEES)
    h1_summary = summarize_yes_no_by_group(resp.reset_index(), "firm_size", "CE")
    diverging_yes_no_plot(h1_summary, "firm_size", "H1: Unternehmensgröße (Q2) vs. CE umgesetzt (Q11)")
else:
    print("H1 skipped: employee-size question text not found. Update Q2_EMPLOYEES to your exact wording.")

# -----------------------------
# 4) H2: Branche (multi-select) vs CE
# -----------------------------
Q4_INDUSTRY = "In welcher Branche ordnen Sie Ihre Tätigkeit ein?"

def h2_industry_summary(df: pd.DataFrame, ce_series: pd.Series, qtext_industry: str):
    industries = get_multi_choice_rows(df, qtext_industry)
    ce_tbl = ce_series.rename("CE").reset_index().rename(columns={"respondent_id": "respondent_id"})
    merged = industries.merge(ce_tbl, on="respondent_id", how="left").dropna(subset=["CE"])
    g = merged.groupby("option")["CE"]
    out = pd.DataFrame({
        "industry": g.size().index,
        "n": g.size().values,
        "yes": g.sum().values
    })
    out["no"] = out["n"] - out["yes"]
    out["yes_pct"] = (out["yes"] / out["n"]) * 100
    out["no_pct"] = (out["no"] / out["n"]) * 100
    return out

if (df["question_text"] == Q4_INDUSTRY).any():
    h2_summary = h2_industry_summary(df, resp["CE"], Q4_INDUSTRY)
    diverging_yes_no_plot(h2_summary.rename(columns={"industry": "industry"}), "industry", "H2: Branche (Q4) vs. CE umgesetzt (Q11)")
else:
    print("H2 skipped: industry question text not found. Update Q4_INDUSTRY to your exact wording.")

# -----------------------------
# 5) H4: Likert coding + Radar (one line, top 5 dimensions)
# -----------------------------
LIKERT_HEMMNIS = {
    "Kein Hemmnis": 1,
    "Geringes Hemmnis": 2,
    "Mittleres Hemmnis": 3,
    "Starkes Hemmnis": 4,
    "Sehr starkes Hemmnis": 5,
    "Keine Antwort": np.nan
}

LIKERT_ZUSTIMMUNG = {
    "Keine Zustimmung": 1,
    "Geringe Zustimmung": 2,
    "Teilweise Zustimmung": 3,
    "Hohe Zustimmung": 4,
    "Sehr hohe Zustimmung": 5,
    "Keine Antwort": np.nan
}

QH4_BLOCK1 = "In welchem Maß stellen die folgenden Punkte ein Hemmnis für die Umsetzung von Kreislaufwirtschaft in Ihrem Unternehmen dar?"
QH4_BLOCK2 = "Inwieweit stimmen Sie folgenden Aussagen zur Umsetzung von Kreislaufwirtschaft bezogen auf die Wettbewerbsfähigkeit aus der Sicht Ihres Unternehmens zu?"
QH4_BLOCK3 = "In welchen Lebenszyklusphasen bzw. Elementen des zirkulären Wertschöpfungsprozesses sehen Sie die größten Hemmnisse für die Umsetzung zirkulärer Wertschöpfungsprozesse?"

def likert_means(df: pd.DataFrame, qtext: str, scale_map: dict) -> pd.DataFrame:
    sub = df[df["question_text"] == qtext].copy()
    if sub.empty:
        return pd.DataFrame(columns=["item", "mean", "pct", "n_valid"])
    sub["value"] = sub["answer"].map(scale_map)
    g = sub.groupby("item")["value"]
    out = pd.DataFrame({
        "item": g.mean().index,
        "mean": g.mean().values,
        "n_valid": g.count().values
    })
    # Convert 1..5 -> 0..100%
    out["pct"] = ((out["mean"] - 1) / 4) * 100
    return out.sort_values("pct", ascending=False)

def radar_one_line(labels, values_pct, title):
    labels = list(labels)
    values = list(values_pct)
    # close the loop
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    fig = plt.figure(figsize=(8, 8))
    ax = plt.subplot(111, polar=True)
    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.15)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_title(title, y=1.08)
    plt.tight_layout()
    plt.show()

# Choose which H4 block you want to visualize:
# - block 1: general barriers (many items)
# - block 2: competitiveness statements
# - block 3: lifecycle phases (nice for radar)
chosen_block = QH4_BLOCK3
chosen_map = LIKERT_HEMMNIS  # block 3 uses Hemmnis scale

means = likert_means(df, chosen_block, chosen_map)

if not means.empty:
    top5 = means.head(5).copy()
    # Make labels shorter for radar
    top5["short"] = top5["item"].apply(lambda s: "\n".join(textwrap.wrap(str(s), width=18)))
    radar_one_line(top5["short"], top5["pct"], f"H4: Top-5 Hemmnisse (Radar) – {chosen_block}")
else:
    print("H4 skipped: chosen H4 question text not found. Update chosen_block to your exact wording.")
