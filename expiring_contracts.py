"""Cato Outbound Engine - step 5a: contracts of target accounts ending in the next months.

Takes every award won by an account in data/accounts_scored.csv (all years, aggiudicatari_full)
and the contract end date declared at contract start (ANAC dataset avvio-contratto).
Keeps contracts ending Nov 2026 - Jul 2027: the renewal tender is the reason to call now.
Extensions and renewals are not in the data, so these are declared end dates, not estimates.

Output: data/expiring_raw.csv (cig, codice_fiscale, data_termine_contrattuale)
Next: fetch_cig_details.py adds object, value and contracting authority for each CIG.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw")
WINDOW = ("2026-11-01", "2027-07-31")


def read_filtered(zip_name, cols, key, keep):
    parts = [ch[ch[key].isin(keep)] for ch in pd.read_csv(os.path.join(RAW, zip_name), sep=";", dtype=str,
                                                           usecols=cols, chunksize=1_000_000)]
    return pd.concat(parts)


def main():
    vats = set(pd.read_csv(os.path.join(DATA, "accounts_scored.csv"), dtype={"vat_number": str})["vat_number"])
    wins = read_filtered("aggiudicatari_full.zip", ["cig", "codice_fiscale"], "codice_fiscale", vats).drop_duplicates()
    ends = (read_filtered("avvio-contratto.zip", ["cig", "data_termine_contrattuale"], "cig", set(wins["cig"]))
            .dropna().drop_duplicates("cig"))
    m = wins.merge(ends, on="cig")
    out = m[(m["data_termine_contrattuale"] >= WINDOW[0]) & (m["data_termine_contrattuale"] <= WINDOW[1])]
    out.to_csv(os.path.join(DATA, "expiring_raw.csv"), index=False)
    print(f"{len(wins):,} wins, {len(m):,} with end date -> {len(out):,} ending {WINDOW[0]} - {WINDOW[1]} "
          f"for {out['codice_fiscale'].nunique():,} companies")


if __name__ == "__main__":
    main()
