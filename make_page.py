"""Cato Outbound Engine - step 6: build the demo page from demo_template.html.

Fills: /*DATA*/ (top 20 table), /*EXPLORER*/ (all accounts), /*EXAMPLES*/, /*N_ACC*/, /*N_EXP*/, /*N_EXP_ACC*/.
Output: cato_outbound_engine.html (artifact, also copied to the CV deliverables folder) and index.html (GitHub Pages)
"""
import json
import os
import shutil

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DELIVERABLES = r"C:\Users\Vincenzo\OneDrive\Documenti\CV\cover letters\cato_gtm"
EXAMPLE_NAMES = ["Ab Medica", "Movi", "Effebi Hospital", "Lamonea Medical"]
STANDALONE_HEAD = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
                   '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                   '<meta name="robots" content="noindex">\n{head}\n</head>\n<body>\n')


def js(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def main():
    top = pd.read_csv(os.path.join(DATA, "cato_top50_hubspot.csv"), dtype=str).head(20)
    table = [{"c": r["Company name"], "d": r["Company Domain Name"],
              "e": r["Number of Employees"] if isinstance(r["Number of Employees"], str) else "",
              "l": int(r["Tender lots bid (2025)"]), "a": int(r["Contracting authorities"]),
              "s": int(float(r["ICP score"])),
              "src": "V" if r["Domain source"].startswith("Claygent") else "G", "o": r["Opener (AI, Clay)"]}
             for _, r in top.iterrows()]

    with open(os.path.join(DATA, "explorer.json"), encoding="utf-8") as f:
        acc = json.load(f)
    names = [a["n"].lower() for a in acc]
    examples = [next(i for i, n in enumerate(names) if n.startswith(e.lower())) for e in EXAMPLE_NAMES]
    n_exp = sum(a["x"]["n"] for a in acc if "x" in a)
    n_exp_acc = sum("x" in a for a in acc)

    page = open(os.path.join(HERE, "demo_template.html"), encoding="utf-8").read()
    for key, val in {"/*DATA*/": js(table), "/*EXPLORER*/": js(acc), "/*EXAMPLES*/": js(examples),
                     "/*N_ACC*/": f"{len(acc):,}".replace(",", "."), "/*N_EXP*/": f"{n_exp:,}".replace(",", "."),
                     "/*N_EXP_ACC*/": f"{n_exp_acc:,}".replace(",", ".")}.items():
        assert key in page, key
        page = page.replace(key, val)
    out = os.path.join(HERE, "cato_outbound_engine.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    shutil.copy(out, os.path.join(DELIVERABLES, "cato_outbound_engine.html"))
    # GitHub Pages serves the file as is, so it needs the document skeleton the artifact host adds
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        cut = page.index("</style>") + len("</style>")  # title, fonts and styles go in <head>
        f.write(STANDALONE_HEAD.format(head=page[:cut]) + page[cut:] + "\n</body>\n</html>\n")
    print(f"Page: {os.path.getsize(out) / 1e6:.2f} MB | examples {examples} | "
          f"{n_exp} expiring contracts across {n_exp_acc} accounts")


if __name__ == "__main__":
    main()
