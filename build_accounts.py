"""Cato Outbound Engine - step 1: data pipeline.

Builds a target-account list for Cato (AI for Italian public tenders) from ANAC open data:
companies that bid most often on medical-device tenders (CPV 331*) published in 2025.

Inputs  (data/raw, downloaded from dati.anticorruzione.it, CC BY 4.0):
  cig_*.zip                 tender lots (CIG) with CPV, value, contracting authority, region, date
  partecipanti_full.zip     bidders per CIG
  aggiudicatari_full.zip    winners per CIG
Output: data/accounts_raw.csv (one row per company, ready for Clay import)
"""
import glob
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "data", "accounts_raw.csv")

CPV_PREFIX = "331"          # medical equipment, devices, consumables
YEAR = "2025"               # tenders published in 2025 (bidders are recorded after award, so 2026 is still incomplete)
MIN_BIDS = 5                # a company bidding 5+ times a year has a real tender workload
CHUNK = 500_000

CIG_COLS = ["cig", "oggetto_lotto", "importo_lotto", "provincia", "data_pubblicazione",
            "denominazione_amministrazione_appaltante", "sezione_regionale",
            "cod_cpv", "descrizione_cpv"]


def read_csv_zip(path, usecols):
    return pd.read_csv(path, sep=";", usecols=usecols, dtype=str, chunksize=CHUNK,
                       encoding="utf-8", on_bad_lines="skip", low_memory=False)


def load_lots():
    parts = []
    for path in sorted(glob.glob(os.path.join(RAW, "cig_*.zip"))):
        for chunk in read_csv_zip(path, CIG_COLS):
            chunk = chunk[chunk["cod_cpv"].fillna("").str.startswith(CPV_PREFIX)]
            chunk = chunk[chunk["data_pubblicazione"].fillna("").str.startswith(YEAR)]
            parts.append(chunk)
        print(f"{os.path.basename(path)}: {sum(len(p) for p in parts):,} lots so far")
    lots = pd.concat(parts).drop_duplicates("cig", keep="last")
    lots["importo_lotto"] = pd.to_numeric(lots["importo_lotto"], errors="coerce").fillna(0)
    return lots.set_index("cig")


def load_roles(path, cigs):
    parts = []
    for chunk in read_csv_zip(path, ["cig", "codice_fiscale", "denominazione"]):
        parts.append(chunk[chunk["cig"].isin(cigs)])
    return pd.concat(parts).drop_duplicates(["cig", "codice_fiscale"])


def top(s):
    s = s.dropna()
    return s.mode().iat[0] if len(s) else ""


def is_company(cf):
    # 11-digit VAT numbers are companies; 16-char codes are individuals (excluded)
    return cf.str.fullmatch(r"\d{11}")


def main():
    lots = load_lots()
    cigs = set(lots.index)
    print(f"Medical-device lots published in {YEAR}: {len(cigs):,}")

    bids = load_roles(os.path.join(RAW, "partecipanti_full.zip"), cigs)
    wins = load_roles(os.path.join(RAW, "aggiudicatari_full.zip"), cigs)
    bids = bids[is_company(bids["codice_fiscale"].fillna(""))]
    wins = wins[is_company(wins["codice_fiscale"].fillna(""))]
    print(f"Bids: {len(bids):,} | Wins: {len(wins):,}")

    bids = bids.join(lots, on="cig")
    wins = wins.join(lots[["importo_lotto"]], on="cig")

    g = bids.groupby("codice_fiscale")
    acc = pd.DataFrame({
        "company_name": g["denominazione"].agg(top),
        "bids_2025": g["cig"].nunique(),
        "value_bid_eur": g["importo_lotto"].sum().round(0),
        "contracting_authorities": g["denominazione_amministrazione_appaltante"].nunique(),
        "regions": g["sezione_regionale"].nunique(),
        "top_region": g["sezione_regionale"].agg(top),
        "top_cpv": g["descrizione_cpv"].agg(top),
        "last_bid_date": g["data_pubblicazione"].max().str[:10],
    })
    w = wins.groupby("codice_fiscale")
    acc["wins_2025"] = w["cig"].nunique().reindex(acc.index).fillna(0).astype(int)
    acc["value_won_eur"] = w["importo_lotto"].sum().reindex(acc.index).fillna(0).round(0)
    acc["win_rate"] = (acc["wins_2025"] / acc["bids_2025"]).round(2)

    # Example lot for the personalised opener: the largest lot the company bid on
    top_lot = bids.sort_values("importo_lotto").groupby("codice_fiscale").tail(1).set_index("codice_fiscale")
    acc["example_lot"] = top_lot["oggetto_lotto"].str.slice(0, 160)
    acc["example_authority"] = top_lot["denominazione_amministrazione_appaltante"]

    acc = acc[acc["bids_2025"] >= MIN_BIDS].sort_values("bids_2025", ascending=False)
    acc.index.name = "vat_number"
    acc.to_csv(OUT, encoding="utf-8")
    print(f"Accounts with {MIN_BIDS}+ bids: {len(acc):,} -> {OUT}")
    print(acc.head(25)[["company_name", "bids_2025", "wins_2025", "value_bid_eur", "top_region"]].to_string())


if __name__ == "__main__":
    main()
