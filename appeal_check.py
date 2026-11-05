"""
Criterion 4 check: does an appeal always move status to under_review and sit
beside (not over) the original decision in the audit log?

scenarios.py can't express this — it needs the content_id a submission came
back with. Service must be running:  python appeal_check.py [--trials 3]
"""
import argparse
import json
import sys

import requests

import config

sys.stdout.reconfigure(errors="replace")

TEXTS = [
    "I went to the market on Saturday and bought way too many peaches.",
    "The meeting ran long again. Nobody had read the notes beforehand.",
    "My brother fixed the bike chain with a paperclip and a lot of swearing.",
    "We missed the last train, so we walked home along the canal.",
    "The soup needed more salt, but everyone ate it anyway.",
    "I wrote this paragraph myself after lunch, between two phone calls.",
    "The library closes at six on weekdays and at four on Saturdays.",
    "Our cat knocked the plant off the shelf for the third time this week.",
    "It rained all morning, then cleared up just in time for the match.",
    "I still have the first letter she sent me, folded in a drawer.",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--url", default=f"http://{config.HOST}:{config.PORT}")
    args = parser.parse_args()

    for trial in range(1, args.trials + 1):
        ok = 0
        for i, text in enumerate(TEXTS, 1):
            sub = requests.post(f"{args.url}/submit", json={
                "text": text, "creator_id": f"appeal_t{trial}_{i}"}, timeout=90)
            cid = sub.json().get("content_id")
            if sub.status_code != 200 or not cid:
                print(f"  trial {trial} #{i}: submit failed ({sub.status_code})")
                continue
            ap = requests.post(f"{args.url}/appeal", json={
                "content_id": cid, "reasoning": "I wrote this myself."}, timeout=30)
            log = requests.get(f"{args.url}/log?limit=2000", timeout=30).json()["entries"]
            mine = [e for e in log if e.get("content_id") == cid]
            decided = [e for e in mine if e.get("status") == "decided"]
            appeals = [e for e in mine if e.get("event") == "appeal"]
            passed = (ap.status_code == 200
                      and ap.json().get("status") == "under_review"
                      and len(decided) == 1 and len(appeals) == 1
                      and appeals[0].get("status") == "under_review")
            ok += passed
            if not passed:
                print(f"  trial {trial} #{i}: FAIL appeal={ap.status_code} "
                      f"decided={len(decided)} appeals={len(appeals)}")
        print(f"trial {trial}: {ok}/{len(TEXTS)} appeals moved to under_review "
              f"and sit beside the original entry")


if __name__ == "__main__":
    main()
