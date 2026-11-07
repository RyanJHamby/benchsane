"""Load and search knowledge cards. Bundled cards ship in the package; extra directories
(BENCHSANE_KB_PATH, os.pathsep separated, or --kb-dir) add private overlays without a fork."""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from importlib import resources

HEADING = re.compile(r"^## (\S+) — (.+)$")
META = re.compile(r"^(tags|check|status|source): *(.*)$")


@dataclass
class Card:
    id: str
    title: str
    body: str
    tags: list = field(default_factory=list)
    status: str = "unverified"
    source: str = ""
    check: str = ""
    file: str = ""
    origin: str = "bundled"

    def to_dict(self):
        return asdict(self)


def parse(text, file="", origin="bundled"):
    cards, cur, in_meta, body = [], None, False, []

    def flush():
        if cur:
            cur.body = "\n".join(body).strip()
            cards.append(cur)

    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            flush()
            cur, in_meta, body = Card(m.group(1), m.group(2), "", file=file, origin=origin), True, []
            continue
        if cur is None:
            continue
        if in_meta:
            mm = META.match(line)
            if mm:
                k, v = mm.group(1), mm.group(2).strip()
                if k == "tags":
                    cur.tags = [t.strip() for t in v.split(",") if t.strip()]
                else:
                    setattr(cur, k, v)
                continue
            in_meta = False
        body.append(line)
    flush()
    return cards


def load_all(extra_dirs=None):
    cards = {}
    root = resources.files("benchsane") / "kb"
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.name.endswith(".md"):
            for c in parse(entry.read_text(encoding="utf-8"), entry.name):
                cards[c.id] = c
    dirs = list(extra_dirs or [])
    env = os.environ.get("BENCHSANE_KB_PATH")
    if env:
        dirs += [d for d in env.split(os.pathsep) if d]
    for d in dirs:
        for dirpath, _, files in os.walk(d):
            for name in sorted(files):
                if name.endswith(".md"):
                    path = os.path.join(dirpath, name)
                    with open(path, encoding="utf-8") as f:
                        for c in parse(f.read(), path, origin="overlay"):
                            cards[c.id] = c  # Overlays can replace a bundled card.
    return cards


def search(query="", tags=None, cards=None, limit=10):
    cards = cards if cards is not None else load_all()
    words = [w for w in re.findall(r"[a-z0-9_+.#-]+", query.lower())]
    wanted = {t.lower() for t in (tags or [])}
    scored = []
    for c in cards.values():
        ctags = {t.lower() for t in c.tags}
        if wanted and not wanted <= (ctags | ({t for t in wanted} if "all" in ctags else set())):
            continue
        score = 0
        hay_title, hay_body = c.title.lower(), c.body.lower()
        for w in words:
            score += 5 * (w in ctags) + 5 * (w in c.id.lower()) + 3 * (w in hay_title) + 1 * (w in hay_body)
        if words and not score:
            continue
        # Specific matches rank above catch-all cards when filtering only by tag.
        scored.append((score, "all" not in ctags, c))
    scored.sort(key=lambda t: (-t[0], not t[1], t[2].id))
    return [c for _, _, c in scored[:limit]]
