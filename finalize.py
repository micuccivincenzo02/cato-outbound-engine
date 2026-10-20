"""Cato Outbound Engine - step 4: merge the Clay export into the final HubSpot import file.

Input : data/cato_top50_clay.csv (export of the Clay table)
Output: data/cato_top50_hubspot.csv (HubSpot company import, sorted by ICP score v2)

Domain logic (same as the Clay table): if the Google domain passes the name check ("Domain OK"),
keep it and its firmographics; otherwise use the Claygent domain found via name + VAT number.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DOUBTFUL = {"mas-spa.com"}  # Claygent answers that need a manual check before outreach


def main():
    d = pd.read_csv(os.path.join(DATA, "cato_top50_clay.csv"), dtype=str)
    ok = d["Domain OK"].str.lower().eq("true")

    out = pd.DataFrame({
        "Company name": d["Company"].str.strip(),
        "Company Domain Name": d["Domain"].where(ok, d["Sito Ufficiale"]),
        "Number of Employees": d["Employee Count"].where(ok, d["Employee Count (2)"]),
        "Country/Region": d["Country"].where(ok, d["Country (2)"]),
        "LinkedIn Company Page": d["Url"].where(ok, None),
        "Industry": "Medical Devices",
        "Lifecycle Stage": "Lead",
        "VAT number": d["VAT IT"],
        "ICP score": pd.to_numeric(d["ICP score v2"], errors="coerce"),
        "Tender lots bid (2025)": pd.to_numeric(d["Lots bid"].str.replace(".", "", regex=False)),
        "Tender lots won (2025)": pd.to_numeric(d["Lots won"].str.replace(".", "", regex=False)),
        "Contracting authorities": pd.to_numeric(d["Contracting authorities"]),
        "Opener (AI, Clay)": d["Email Apertura"],
        "Domain source": ok.map({True: "Google + name check", False: "Claygent (name + VAT)"}),
        "Data check": "",
        "Source": "ANAC open data (CC BY 4.0) + Clay",
    })
    out.loc[out["Number of Employees"].isna(), "Data check"] = "no firmographics"
    out.loc[out["Company Domain Name"].isin(DOUBTFUL), "Data check"] = "verify domain"
    out = out.sort_values(["ICP score", "Tender lots bid (2025)"], ascending=False)
    out.to_csv(os.path.join(DATA, "cato_top50_hubspot.csv"), index=False, encoding="utf-8-sig")

    print(f"Rows: {len(out)} | Domain OK (Google): {ok.sum()} | fixed by Claygent: {(~ok).sum()}")
    print(f"With firmographics: {out['Number of Employees'].notna().sum()} | flagged: "
          f"{(out['Data check'] != '').sum()}")
    print(out["ICP score"].value_counts().sort_index(ascending=False).to_dict())
    print(out.head(20)[["Company name", "Company Domain Name", "Number of Employees", "ICP score",
                        "Tender lots bid (2025)", "Data check"]].to_string())


if __name__ == "__main__":
    main()
