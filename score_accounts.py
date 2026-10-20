"""Cato Outbound Engine - step 2: ICP scoring (same logic as the Clay formula column).

Calibrated on Cato's public customer logos found in the data: they bid 16-995 times in 2025,
are Italian mid-size companies (not local branches of multinationals with in-house tender teams)
and work with many different contracting authorities.

Input : data/accounts_raw.csv
Output: data/accounts_scored.csv (all accounts), data/cato_top50_hubspot.csv (HubSpot import),
        data/clay_import.csv (raw columns for the Clay table, score rebuilt there as a formula)
"""
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# Cato customers shown on get-cato.com, matched by name in the ANAC data
CUSTOMER_NAME_KEYS = ["MOVI SPA", "LORENZATTO", "FAVERO HEALTH", "KASTER", "VIVISOL", "SOL S.P.A.",
                      "AHSI", "RESPIRAIRE", "EXACTA LABCENTER"]
# Branches of multinationals: generic name markers + well-known global medtech brands
MULTINATIONAL = re.compile(r"\b(ITALIA|ITALY|INTERNATIONAL|EUROPE|GMBH|ABBOTT|BAYER|MOLNLYCKE|LOHMANN|BAXTER|"
                           r"SIEMENS|PHILIPS|FRESENIUS|3M|CONVATEC|HARTMANN|OLYMPUS|MEDTRONIC|"
                           r"COLOPLAST|ESSITY|DRAEGER|DRAGER|ROCHE|SARTORIUS|TERUMO|CARDINAL)\b")


def score(row):
    bids = row["bids_2025"]
    volume = 40 if 15 <= bids <= 1000 else 20 if bids < 15 else 10     # >1000: in-house tender team
    breadth = min(row["contracting_authorities"], 20)                    # 1 pt per authority, max 20
    win_rate = min(row["wins_2025"] / bids, 1)
    upside = 15 if win_rate < 0.6 else 8                                # room to win more of what they bid
    local = 0 if MULTINATIONAL.search(row["company_name"]) else 25      # Italian mid-size, not a branch
    return volume + breadth + upside + local


def opener(row):
    lot = str(row["example_lot"]).strip().rstrip(".").capitalize()
    return (f"Nel 2025 avete partecipato a {row['bids_2025']} lotti di gara per dispositivi medici "
            f"con {row['contracting_authorities']} stazioni appaltanti diverse, tra cui "
            f"\"{lot[:90]}\" ({str(row['example_authority']).title()}).")


def main():
    acc = pd.read_csv(os.path.join(DATA, "accounts_raw.csv"), dtype={"vat_number": str})
    name = acc["company_name"].str.upper()
    acc["is_cato_customer"] = name.apply(lambda n: any(k in n for k in CUSTOMER_NAME_KEYS))
    acc["icp_score"] = acc.apply(score, axis=1)
    acc["opener_draft"] = acc.apply(opener, axis=1)
    acc = acc.sort_values(["icp_score", "bids_2025"], ascending=False)
    acc.to_csv(os.path.join(DATA, "accounts_scored.csv"), index=False, encoding="utf-8")

    cust = acc[acc["is_cato_customer"]]
    print("Cato customers - score:", cust[["company_name", "icp_score"]].values.tolist())
    print(f"Customers scoring >=80: {(cust['icp_score'] >= 80).sum()}/{len(cust)} "
          f"vs all accounts: {(acc['icp_score'] >= 80).mean():.0%}")

    prospects = acc[~acc["is_cato_customer"]].head(50)
    hubspot = pd.DataFrame({
        "Company name": prospects["company_name"].str.title(),
        "VAT number": prospects["vat_number"],
        "Industry": "Medical Devices",
        "Lifecycle stage": "Lead",
        "ICP score": prospects["icp_score"],
        "Tender lots bid (2025)": prospects["bids_2025"],
        "Tender lots won (2025)": prospects["wins_2025"],
        "Value bid (EUR)": prospects["value_bid_eur"].astype(int),
        "Contracting authorities": prospects["contracting_authorities"],
        "Opener draft": prospects["opener_draft"],
        "Source": "ANAC open data (CC BY 4.0)",
    })
    hubspot.to_csv(os.path.join(DATA, "cato_top50_hubspot.csv"), index=False, encoding="utf-8-sig")
    clay = pd.DataFrame({
        "Company": prospects["company_name"].str.title(),
        "VAT": prospects["vat_number"],
        "Lots bid": prospects["bids_2025"],
        "Lots won": prospects["wins_2025"],
        "Contracting authorities": prospects["contracting_authorities"],
        "Value bid EUR": prospects["value_bid_eur"].astype(int),
        "Example lot": prospects["example_lot"].str.capitalize(),
        "Example authority": prospects["example_authority"].str.title(),
    })
    clay.to_csv(os.path.join(DATA, "clay_import.csv"), index=False, encoding="utf-8-sig")
    print(hubspot.head(20)[["Company name", "ICP score", "Tender lots bid (2025)", "Contracting authorities"]].to_string())
    print("\nExample opener:", hubspot["Opener draft"].iat[0])


if __name__ == "__main__":
    main()
