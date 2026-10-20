"""Cato Outbound Engine - step 5b: download yearly ANAC CIG files one month at a time and keep only the CIGs listed in
data/expiring_raw.csv (contracts of target accounts ending Nov 2026 - Jul 2027).
Each monthly zip is deleted after filtering, so disk use stays small.

Usage: py -I fetch_cig_details.py 2022 2023 2024
Output: data/expiring_cig_details.csv (appends across runs, de-duplicated at the end)
"""
import os
import subprocess
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "data", "expiring_cig_details.csv")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
BASE = "https://dati.anticorruzione.it/opendata/download/dataset/cig-{y}/filesystem/cig_csv_{y}_{m:02d}.zip"
COLS = ["cig", "oggetto_lotto", "oggetto_gara", "importo_lotto", "denominazione_amministrazione_appaltante",
        "sezione_regionale", "data_pubblicazione", "cod_cpv", "descrizione_cpv"]


def main(years):
    wanted = set(pd.read_csv(os.path.join(HERE, "data", "expiring_raw.csv"), dtype=str)["cig"])
    found = []
    for y in years:
        for m in range(1, 13):
            path = os.path.join(RAW, f"tmp_cig_{y}_{m:02d}.zip")
            r = subprocess.run(["curl", "-s", "-f", "-L", "-A", UA, "-o", path, BASE.format(y=y, m=m)])
            if r.returncode != 0:
                print(f"{y}-{m:02d}: missing")
                continue
            n = 0
            for chunk in pd.read_csv(path, sep=";", dtype=str, usecols=COLS, chunksize=500_000,
                                     on_bad_lines="skip", low_memory=False):
                hit = chunk[chunk["cig"].isin(wanted)]
                n += len(hit)
                found.append(hit)
            os.remove(path)
            print(f"{y}-{m:02d}: {n} matches", flush=True)
    new = pd.concat(found) if found else pd.DataFrame(columns=COLS)
    if os.path.exists(OUT):
        new = pd.concat([pd.read_csv(OUT, dtype=str), new])
    new = new.drop_duplicates("cig", keep="last")
    new.to_csv(OUT, index=False)
    print(f"Details for {len(new):,} of {len(wanted):,} expiring CIGs -> {OUT}")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]])
