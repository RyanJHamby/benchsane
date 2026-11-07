from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from importlib import resources

from . import __version__
from . import ab as ab_mod
from . import capture as capture_mod
from . import compare as compare_mod
from . import doctor as doctor_mod
from . import formats
from . import kb as kb_mod

ICON = {"ok": "ok  ", "info": "info", "warn": "WARN", "fail": "FAIL"}


def cmd_doctor(args):
    checks = doctor_mod.run_checks()
    g = doctor_mod.grade(checks)
    if args.json:
        print(json.dumps(doctor_mod.report(checks), indent=1))
    else:
        for c in sorted(checks, key=lambda c: -doctor_mod.ORDER[c.level]):
            print(f"[{ICON[c.level]}] {c.id}: {c.message}")
            if c.fix and c.level in ("warn", "fail"):
                print(f"       fix: {c.fix}")
            if c.card and c.level in ("warn", "fail"):
                print(f"       why: benchsane kb show {c.card}")
        print(f"\nGrade: {g}. {doctor_mod.GRADE_MEANING[g]}")
    if g == "smoke" or (args.strict and g != "clean"):
        return 1
    return 0


def cmd_capture(args):
    text = json.dumps(capture_mod.capture(), indent=1)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Wrote {args.output}")
    else:
        print(text)
    return 0


def cmd_ab(args):
    if not args.aa and not args.b:
        print("Give -b, or use --aa to measure the noise floor of -a.", file=sys.stderr)
        return 2
    if args.out and os.path.exists(os.path.join(args.out, "samples.json")):
        print(f"{args.out} already has results; choose a new directory.", file=sys.stderr)
        return 2
    cpus = {int(x) for x in args.cpus.split(",")} if args.cpus else None

    def progress(i, n):
        print(f"\rblock {i}/{n}", end="", file=sys.stderr, flush=True)

    try:
        r, env = ab_mod.run_ab(args.a, None if args.aa else args.b, runs=args.runs, warmup=args.warmup, seed=args.seed, out=args.out,
                               shell=args.shell, env_pad=args.env_pad, cpus=cpus, min_effect=args.min_effect, redact=args.redact_commands, progress=progress)
    except RuntimeError as e:
        print(f"\nAborted: {e}", file=sys.stderr)
        return 1
    print(file=sys.stderr)
    if args.json:
        print(json.dumps({k: v for k, v in r.items() if k not in ("samples", "order")}, indent=1))
    else:
        print(ab_mod.render_report(r, env))
    return 0


def cmd_compare(args):
    try:
        r = compare_mod.compare(args.baseline, args.candidate, args.select_baseline, args.select_candidate, args.min_effect)
    except (compare_mod.LoadError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, indent=1))
    else:
        c = r["comparison"]
        print(f"{formats.VERDICT_TEXT[c['verdict']]} {formats.describe(c)}.")
        print(f"Baseline:  n={c['n_baseline']} median={formats.fmt_value(r['baseline']['summary']['median'])} cv={r['baseline']['summary']['cv'] * 100:.2f}%")
        print(f"Candidate: n={c['n_candidate']} median={formats.fmt_value(r['candidate']['summary']['median'])} cv={r['candidate']['summary']['cv'] * 100:.2f}%")
        print(f"Claim: {r['claim']}")
        for w in r["warnings"]:
            print(f"warning: {w}")
    if args.fail_on_regression and r["comparison"]["verdict"] == "slower":
        return 3
    return 0


def cmd_export(args):
    with open(args.result, encoding="utf-8") as f:
        result = json.load(f)
    if not str(result.get("schema", "")).startswith("benchsane.result/"):
        print(f"{args.result} isn't a benchsane result file (samples.json from `ab`).", file=sys.stderr)
        return 2
    if args.to == "csv":
        print(formats.to_csv(result), end="")
    elif args.to == "bmf":
        print(json.dumps(formats.to_bmf(result, args.name), indent=1))
    elif args.to == "github-benchmark":
        print(json.dumps(formats.to_github_benchmark(result, args.name), indent=1))
    elif args.to == "claim":
        print(result["claim"])
    return 0


def cmd_schema(args):
    print((resources.files("benchsane") / "schemas" / f"{args.name}.schema.json").read_text(encoding="utf-8"), end="")
    return 0


def cmd_kb(args):
    cards = kb_mod.load_all(args.kb_dir)
    if args.kb_cmd == "show":
        card = cards.get(args.id)
        if not card:
            print(f"Unknown card {args.id!r}. Try: benchsane kb search {args.id}", file=sys.stderr)
            return 2
        print(f"{card.id}: {card.title}\nstatus: {card.status}  tags: {', '.join(card.tags)}")
        if card.source:
            print("source: " + "\n        ".join(card.source.split()))
        print(f"\n{card.body}")
        return 0
    if args.kb_cmd == "tags":
        counts = {}
        for c in cards.values():
            for t in c.tags:
                counts[t] = counts.get(t, 0) + 1
        for t, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"{n:4} {t}")
        return 0
    query = " ".join(args.query) if args.kb_cmd == "search" else ""
    tags = args.tag or []
    found = kb_mod.search(query, tags, cards, limit=args.limit)
    if args.json:
        print(json.dumps([c.to_dict() for c in found], indent=1))
    else:
        for c in found:
            flag = "" if c.status == "cited" else " (unverified)"
            print(f"{c.id:32} {c.title}{flag}")
        if not found:
            print("No matches.")
    return 0


def cmd_init(args):
    dest = os.path.join(args.dir, "bench")
    os.makedirs(os.path.join(dest, "runs"), exist_ok=True)
    src = resources.files("benchsane") / "templates" / "PLAN.md"
    target = os.path.join(dest, "PLAN.md")
    if os.path.exists(target):
        print(f"{target} already exists; leaving it alone.")
    else:
        with open(target, "w", encoding="utf-8") as f:
            f.write(src.read_text(encoding="utf-8"))
        print(f"Wrote {target}")
    return 0


def cmd_install_skill(args):
    dest = os.path.join(args.dir or os.path.join(".claude", "skills"), "benchsane")
    if os.path.exists(dest) and not args.force:
        print(f"{dest} already exists; pass --force to replace it.", file=sys.stderr)
        return 2
    os.makedirs(dest, exist_ok=True)
    src = resources.files("benchsane") / "skill" / "SKILL.md"
    with open(os.path.join(dest, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(src.read_text(encoding="utf-8"))
    print(f"Installed skill to {dest}")
    return 0


def parser():
    p = argparse.ArgumentParser(prog="benchsane", description="Measure programs and hardware without fooling yourself.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="read-only check of whether this machine is ready to measure")
    d.add_argument("--json", action="store_true")
    d.add_argument("--strict", action="store_true", help="exit 1 on any warning")
    d.set_defaults(fn=cmd_doctor)

    c = sub.add_parser("capture", help="write an environment manifest")
    c.add_argument("-o", "--output")
    c.set_defaults(fn=cmd_capture)

    a = sub.add_parser("ab", help="randomized, interleaved A/B (or A/A) in fresh processes")
    a.add_argument("-a", required=True, help="baseline command")
    a.add_argument("-b", help="candidate command")
    a.add_argument("--aa", action="store_true", help="compare -a against itself to measure the noise floor")
    a.add_argument("--runs", type=int, default=30)
    a.add_argument("--warmup", type=int, default=2)
    a.add_argument("--seed", type=int)
    a.add_argument("--out", help="directory for samples.json, env.json and report.md")
    a.add_argument("--shell", action="store_true", help="run through a shell, adding its overhead")
    a.add_argument("--env-pad", action="store_true", help="vary environment size per block to sample layout bias")
    a.add_argument("--cpus", help="pin to CPUs, e.g. 2,3 (Linux)")
    a.add_argument("--min-effect", type=float, default=0.01)
    a.add_argument("--redact-commands", action="store_true", help="leave command strings out of outputs")
    a.add_argument("--json", action="store_true")
    a.set_defaults(fn=cmd_ab)

    m = sub.add_parser("compare", help="compare two result files")
    m.add_argument("baseline")
    m.add_argument("candidate")
    m.add_argument("--select-baseline")
    m.add_argument("--select-candidate")
    m.add_argument("--min-effect", type=float, default=0.01)
    m.add_argument("--fail-on-regression", action="store_true", help="exit 3 if the candidate is slower")
    m.add_argument("--json", action="store_true")
    m.set_defaults(fn=cmd_compare)

    e = sub.add_parser("export", help="convert samples.json for other tools")
    e.add_argument("result", help="samples.json from `benchsane ab`")
    e.add_argument("--to", required=True, choices=["csv", "bmf", "github-benchmark", "claim"])
    e.add_argument("--name", help="benchmark name prefix for bmf and github-benchmark")
    e.set_defaults(fn=cmd_export)

    h = sub.add_parser("schema", help="print a JSON Schema for benchsane's outputs")
    h.add_argument("name", choices=["result", "comparison", "doctor", "env"])
    h.set_defaults(fn=cmd_schema)

    k = sub.add_parser("kb", help="search the knowledge base")
    k.add_argument("--kb-dir", action="append", help="extra directory of private cards; repeatable")
    ks = k.add_subparsers(dest="kb_cmd", required=True)
    s = ks.add_parser("search")
    s.add_argument("query", nargs="*")
    s.add_argument("--tag", action="append")
    s.add_argument("--limit", type=int, default=15)
    s.add_argument("--json", action="store_true")
    l = ks.add_parser("list")
    l.add_argument("--tag", action="append")
    l.add_argument("--limit", type=int, default=1000)
    l.add_argument("--json", action="store_true")
    sh = ks.add_parser("show")
    sh.add_argument("id")
    ks.add_parser("tags")
    k.set_defaults(fn=cmd_kb)

    i = sub.add_parser("init", help="add bench/PLAN.md to a project")
    i.add_argument("dir", nargs="?", default=".")
    i.set_defaults(fn=cmd_init)

    n = sub.add_parser("install-skill", help="copy the agent skill into a project")
    n.add_argument("--dir", help="skills directory (default .claude/skills)")
    n.add_argument("--force", action="store_true")
    n.set_defaults(fn=cmd_install_skill)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
