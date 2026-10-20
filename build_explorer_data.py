"""Cato Outbound Engine - step 5c: data for the interactive explorer on the demo page.

For each of the accounts in data/accounts_scored.csv (5+ medical-device lots in 2025):
monthly lots, top contracting authorities, score breakdown, top competitors (companies bidding
on the same lots), contracts ending Nov 2026 - Jul 2027, Clay enrichment for the top 50, opener.

Output: data/explorer.json (compact keys, read by the demo page)
"""
import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # sibling modules under `py -I`
from build_accounts import RAW, is_company, load_lots, load_roles
from score_accounts import CUSTOMER_NAME_KEYS, MULTINATIONAL

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
WINDOW = ("2026-11-01", "2027-07-31")
MONTHS_IT = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]


def clean_name(name):
    name = re.sub(r"\s+", " ", str(name)).strip()
    name = re.sub(r"(?i)\s+societa' a responsabilita' limitata.*$", " S.r.l.", name)
    return name.title().replace("S.R.L.", "S.r.l.").replace("S.P.A.", "S.p.A.").replace("Srl", "S.r.l.")


def month_label(iso):
    return f"{MONTHS_IT[int(iso[5:7]) - 1]} {iso[:4]}"


def score_parts(r):
    bids = r["bids_2025"]
    volume = 40 if 15 <= bids <= 1000 else 20 if bids < 15 else 10
    breadth = min(int(r["contracting_authorities"]), 20)
    upside = 15 if min(r["wins_2025"] / bids, 1) < 0.6 else 8
    local = 0 if MULTINATIONAL.search(r["company_name"]) else 25
    return [volume, breadth, upside, local]


def expiring_by_vat():
    raw_path, det_path = os.path.join(DATA, "expiring_raw.csv"), os.path.join(DATA, "expiring_cig_details.csv")
    if not (os.path.exists(raw_path) and os.path.exists(det_path)):
        return {}
    e = pd.read_csv(raw_path, dtype=str).merge(pd.read_csv(det_path, dtype=str), on="cig")
    e = e[(e["data_termine_contrattuale"] >= WINDOW[0]) & (e["data_termine_contrattuale"] <= WINDOW[1])]
    e["importo_lotto"] = pd.to_numeric(e["importo_lotto"], errors="coerce").fillna(0)
    e["obj"] = e["oggetto_lotto"].where(e["oggetto_lotto"].str.len() > 12, e["oggetto_gara"]).fillna("")
    out = {}
    for vat, g in e.sort_values("data_termine_contrattuale").groupby("codice_fiscale"):
        out[vat] = {
            "n": len(g),
            "v": int(g["importo_lotto"].sum()),
            "list": [[r.data_termine_contrattuale[:7], str(r.denominazione_amministrazione_appaltante).title(),
                      str(r.obj).strip().capitalize()[:110], int(r.importo_lotto)]
                     for r in g.nlargest(4, "importo_lotto").sort_values("data_termine_contrattuale").itertuples()],
        }
    return out


def opener(r, exp):
    if exp:
        first = exp["list"][0]
        obj = first[2] if len(first[2]) <= 70 else first[2][:70].rsplit(" ", 1)[0].rstrip(",;-") + "…"
        return (f"Il vostro contratto per \"{obj}\" con {first[1]} risulta in scadenza a "
                f"{month_label(first[0])}: la gara di rinnovo è vicina, e nel 2025 avete già partecipato a "
                f"{r['bids_2025']} lotti di gara per dispositivi medici.")
    return (f"Nel 2025 avete partecipato a {r['bids_2025']} lotti di gara per dispositivi medici con "
            f"{r['contracting_authorities']} stazioni appaltanti diverse.")


def main():
    acc = pd.read_csv(os.path.join(DATA, "accounts_scored.csv"), dtype={"vat_number": str})
    acc = acc.sort_values(["icp_score", "bids_2025"], ascending=False).reset_index(drop=True)
    idx = {v: i for i, v in enumerate(acc["vat_number"])}

    lots = load_lots()
    bids = load_roles(os.path.join(RAW, "partecipanti_full.zip"), set(lots.index))
    bids = bids[is_company(bids["codice_fiscale"].fillna(""))][["cig", "codice_fiscale"]]
    bids = bids[bids["codice_fiscale"].isin(idx)]
    bids = bids.join(lots[["data_pubblicazione", "denominazione_amministrazione_appaltante"]], on="cig")

    monthly = (bids.assign(m=bids["data_pubblicazione"].str[5:7].astype(int))
               .groupby(["codice_fiscale", "m"]).size().unstack(fill_value=0)
               .reindex(columns=range(1, 13), fill_value=0))
    top_auth = (bids.groupby(["codice_fiscale", "denominazione_amministrazione_appaltante"]).size()
                .rename("n").reset_index().sort_values("n", ascending=False).groupby("codice_fiscale").head(3))

    pairs = bids.merge(bids, on="cig")
    pairs = pairs[pairs["codice_fiscale_x"] != pairs["codice_fiscale_y"]]
    comp = (pairs.groupby(["codice_fiscale_x", "codice_fiscale_y"]).size().rename("n").reset_index()
            .sort_values("n", ascending=False).groupby("codice_fiscale_x").head(5))

    clay_path = os.path.join(DATA, "cato_top50_hubspot.csv")
    clay = pd.read_csv(clay_path, dtype=str).set_index("VAT number") if os.path.exists(clay_path) else pd.DataFrame()
    expiring = expiring_by_vat()

    rows = []
    for i, r in acc.iterrows():
        vat = r["vat_number"]
        exp = expiring.get(vat)
        row = {
            "n": clean_name(r["company_name"]), "vat": vat,
            "b": int(r["bids_2025"]), "w": int(r["wins_2025"]), "a": int(r["contracting_authorities"]),
            "val": int(r["value_bid_eur"]), "cpv": str(r["top_cpv"]).capitalize()[:60],
            "s": int(r["icp_score"]), "sp": score_parts(r),
            "m": [int(x) for x in monthly.loc[vat]] if vat in monthly.index else [0] * 12,
            "ta": [[str(t).title(), int(n)] for t, n in
                   top_auth[top_auth["codice_fiscale"] == vat][["denominazione_amministrazione_appaltante", "n"]].values],
            "c": [[idx[c], int(n)] for c, n in comp[comp["codice_fiscale_x"] == vat][["codice_fiscale_y", "n"]].values],
            "cust": bool(r["is_cato_customer"]),
            "o": opener(r, exp),
        }
        if exp:
            row["x"] = exp
        if vat in clay.index:
            c = clay.loc[vat]
            row["d"] = c["Company Domain Name"]
            row["emp"] = c["Number of Employees"] if isinstance(c["Number of Employees"], str) else ""
            row["oc"] = c["Opener (AI, Clay)"]
        rows.append(row)

    with open(os.path.join(DATA, "explorer.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    size = os.path.getsize(os.path.join(DATA, "explorer.json"))
    print(f"{len(rows)} accounts, {sum('x' in r for r in rows)} with expiring contracts, "
          f"{sum(bool(r['c']) for r in rows)} with competitors -> explorer.json ({size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
