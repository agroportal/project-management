#!/usr/bin/env python3
"""Detect duplicate agents in AgroPortal and open/refresh a tracking issue.

Runs from a GitHub Action (see .github/workflows/agent-duplicates.yml) but can
also be run locally.

Detection (high confidence): agents whose *name* collapses to the same value
after trimming, Unicode-folding accents and lower-casing are considered the
same agent recorded several times. A secondary, lower-confidence pass flags
reversed first/last names and near-identical spellings for manual review.

GitHub side effects (skipped when DRY_RUN=1):
  * duplicates found + no open bot issue   -> create a new issue
  * duplicates found + open bot issue      -> refresh its body + add a comment
  * no duplicates   + open bot issue       -> comment and close it
  * no duplicates   + no open bot issue    -> do nothing

Environment variables:
  AGROPORTAL_API_KEY   API key for data.agroportal.eu (required unless AGENTS_JSON_FILE)
  AGROPORTAL_API_BASE  default https://data.agroportal.eu
  GITHUB_REPOSITORY    owner/repo (provided by Actions)
  GH_TOKEN             token used by the gh CLI (provided by Actions)
  ISSUE_TITLE          stable title used to find/refresh the bot issue
  LABELS               comma-separated labels (default "content,metadata")
  ASSIGNEES            comma-separated logins (default "jonquet,asbage")
  AGENTS_JSON_FILE     read agents from this local file instead of HTTP (testing)
  DRY_RUN              "1" to print intended GitHub actions without performing them
"""
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher

API_BASE = os.environ.get("AGROPORTAL_API_BASE", "https://data.agroportal.eu").rstrip("/")
API_KEY = os.environ.get("AGROPORTAL_API_KEY", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "Doublons d'agents AgroPortal (détection automatique)")
LABELS = [x.strip() for x in os.environ.get("LABELS", "content,metadata").split(",") if x.strip()]
ASSIGNEES = [x.strip() for x in os.environ.get("ASSIGNEES", "jonquet,asbage").split(",") if x.strip()]
AGENTS_JSON_FILE = os.environ.get("AGENTS_JSON_FILE", "")
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"
MARKER = "<!-- agroportal-agent-duplicate-bot -->"


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def fetch_agents():
    """Return the full list of agents, following pagination."""
    if AGENTS_JSON_FILE:
        with open(AGENTS_JSON_FILE, encoding="utf-8") as fh:
            return json.load(fh)["collection"]
    if not API_KEY:
        sys.exit("AGROPORTAL_API_KEY is required (or set AGENTS_JSON_FILE for testing).")
    # Pass the key via the Authorization header, never in the URL: this repo is
    # public, so a traceback that echoes the URL must not leak the key.
    headers = {"Accept": "application/json", "Authorization": f"apikey token={API_KEY}"}
    agents, page = [], 1
    while True:
        qs = urllib.parse.urlencode({"page": page, "pagesize": 2000})
        req = urllib.request.Request(f"{API_BASE}/agents?{qs}", headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.load(resp)
        agents.extend(data.get("collection", []))
        nxt = data.get("nextPage")
        if not nxt:
            break
        page = nxt
    return agents


# --------------------------------------------------------------------------- #
# Detection
# --------------------------------------------------------------------------- #
def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def enrichment(a):
    parts = []
    if a.get("identifiers"):
        parts.append("ORCID/ROR")
    if a.get("email"):
        parts.append("email")
    return "+".join(parts) or "—"


def group_by_name(agents):
    """Return high-confidence duplicate groups, sorted like the original report."""
    buckets = defaultdict(dict)  # key -> {agent id: agent}  (de-dupes identical ids)
    for a in agents:
        key = norm(a.get("name"))
        if key:
            buckets[key][a["id"]] = a
    groups = [(k, list(v.values())) for k, v in buckets.items() if len(v) > 1]
    groups.sort(key=lambda kv: (-len(kv[1]), kv[0]))
    return groups


def secondary_matches(agents):
    """Lower-confidence: reversed first/last names and near-identical spellings."""
    uniq = sorted({norm(a["name"]) for a in agents if norm(a.get("name"))})
    reversed_pairs, fuzzy_pairs, grouped = [], [], set()
    tok = defaultdict(list)
    for n in uniq:
        tok[" ".join(sorted(n.split()))].append(n)
    for names in tok.values():
        if len(names) > 1:
            reversed_pairs.append(names)
            grouped.update(names)
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            a, b = uniq[i], uniq[j]
            if a in grouped or b in grouped or abs(len(a) - len(b)) > 3:
                continue
            if SequenceMatcher(None, a, b).ratio() >= 0.90:
                fuzzy_pairs.append((a, b))
    return reversed_pairs, fuzzy_pairs


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def uuid_of(a):
    return a["id"].rstrip("/").split("/")[-1]


def cell(a):
    return f"`{a.get('name')}` [{enrichment(a)}] `{uuid_of(a)}`"


def build_body(agents, groups, reversed_pairs, fuzzy_pairs):
    redundant = sum(len(v) - 1 for _, v in groups)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = [
        MARKER,
        f"# Doublons d'agents AgroPortal — {len(groups)} groupes",
        "",
        f"_Détection automatique du {now} — source : "
        f"[`{API_BASE}/agents`]({API_BASE}/agents). "
        f"{len(agents)} agents analysés, **{redundant} enregistrements redondants**._",
        "",
        "⭐ = enregistrement le plus complet (master recommandé à conserver, "
        "c.-à-d. celui qui porte un identifiant externe ORCID/ROR et/ou un email).",
        "",
        "| # | Nom | Type | Master (⭐) — UUID | Doublon(s) à fusionner — UUID |",
        "|---|-----|------|--------------------|-------------------------------|",
    ]
    for i, (_, v) in enumerate(groups, 1):
        ordered = sorted(v, key=lambda a: (bool(a.get("identifiers")), bool(a.get("email"))), reverse=True)
        master, others = ordered[0], ordered[1:]
        warn = " ⚠️type" if len({a.get("agentType") for a in v}) > 1 else ""
        name = (master.get("name") or "").strip()
        master_cell = f"⭐ `{name}` [{enrichment(master)}] · `{uuid_of(master)}`"
        others_cell = " · ".join(cell(a) for a in others)
        out.append(f"| {i} | **{name}**{warn} | {master.get('agentType')} | {master_cell} | {others_cell} |")

    if reversed_pairs or fuzzy_pairs:
        out += ["", "<details>", "<summary>Cas à vérifier manuellement "
                "(inversions nom/prénom, quasi-doublons — peut inclure des faux positifs)</summary>", ""]
        for names in reversed_pairs:
            out.append(f"- **Ordre nom/prénom inversé** : {' ↔ '.join(f'`{n}`' for n in names)}")
        for a, b in fuzzy_pairs:
            out.append(f"- **Quasi-doublon** : `{a}` ↔ `{b}`")
        out += ["", "</details>"]

    out += ["", "---", "_Issue gérée automatiquement par "
            "`scripts/check_agent_duplicates.py`. Elle est rafraîchie chaque semaine "
            "et fermée automatiquement lorsqu'aucun doublon n'est détecté._"]
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# GitHub side effects
# --------------------------------------------------------------------------- #
def gh(*args, check=True, capture=False):
    print("+ gh " + " ".join(args))
    if DRY_RUN:
        return ""
    res = subprocess.run(["gh", *args], text=True,
                         capture_output=capture, check=False)
    if capture and res.stdout:
        print(res.stdout.strip())
    if res.returncode != 0:
        sys.stderr.write((res.stderr or "") + "\n")
        if check:
            sys.exit(f"gh command failed: gh {' '.join(args)}")
    return res.stdout if capture else ""


def find_open_issue():
    """Return the number of the open bot issue (exact title match) or None."""
    if DRY_RUN:
        return None
    out = subprocess.run(
        ["gh", "issue", "list", "--repo", REPO, "--state", "open",
         "--search", f'"{ISSUE_TITLE}" in:title', "--json", "number,title"],
        text=True, capture_output=True, check=False,
    ).stdout or "[]"
    for it in json.loads(out):
        if it.get("title") == ISSUE_TITLE:
            return it["number"]
    return None


def write_body(body):
    path = os.path.join(os.environ.get("RUNNER_TEMP", "."), "agent_dupes_body.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return path


def create_issue(body):
    body_file = write_body(body)
    args = ["issue", "create", "--repo", REPO, "--title", ISSUE_TITLE, "--body-file", body_file]
    for lb in LABELS:
        args += ["--label", lb]
    for asg in ASSIGNEES:
        args += ["--assignee", asg]
    print("Creating a new tracking issue.")
    gh(*args, capture=True)


def refresh_issue(number, body, n_groups):
    body_file = write_body(body)
    print(f"Refreshing existing issue #{number}.")
    args = ["issue", "edit", str(number), "--repo", REPO, "--body-file", body_file]
    for lb in LABELS:
        args += ["--add-label", lb]
    for asg in ASSIGNEES:
        args += ["--add-assignee", asg]
    gh(*args, check=False, capture=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    gh("issue", "comment", str(number), "--repo", REPO,
       "--body", f"🔁 Rafraîchi le {today} : **{n_groups} groupes** de doublons toujours présents.",
       check=False)


def close_issue(number):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"No duplicates left; closing issue #{number}.")
    gh("issue", "comment", str(number), "--repo", REPO,
       "--body", f"✅ Aucun doublon d'agent détecté le {today}. Fermeture automatique.", check=False)
    gh("issue", "close", str(number), "--repo", REPO, "--reason", "completed", check=False)


# --------------------------------------------------------------------------- #
def main():
    agents = fetch_agents()
    groups = group_by_name(agents)
    reversed_pairs, fuzzy_pairs = secondary_matches(agents)
    redundant = sum(len(v) - 1 for _, v in groups)
    print(f"Analysed {len(agents)} agents -> {len(groups)} duplicate groups, "
          f"{redundant} redundant records.")

    existing = find_open_issue()

    if groups:
        body = build_body(agents, groups, reversed_pairs, fuzzy_pairs)
        if DRY_RUN:
            print("\n----- issue body (dry-run) -----\n" + body)
        if existing:
            refresh_issue(existing, body, len(groups))
        else:
            create_issue(body)
    else:
        print("No duplicate agents detected.")
        if existing:
            close_issue(existing)

    # GitHub Actions step summary
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"### Agent duplicate detection\n\n"
                     f"- Agents analysés : **{len(agents)}**\n"
                     f"- Groupes de doublons : **{len(groups)}**\n"
                     f"- Enregistrements redondants : **{redundant}**\n")


if __name__ == "__main__":
    main()
