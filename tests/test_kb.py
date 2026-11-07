import re
from pathlib import Path

from benchsane import doctor, kb


def test_cards_are_valid():
    cards = kb.load_all()
    assert len(cards) >= 100
    for c in cards.values():
        assert c.tags, c.id
        assert c.status in ("cited", "unverified"), c.id
        assert c.body, c.id
        if c.status == "cited":
            assert c.source, c.id
        assert all(u.startswith("http") for u in c.source.split()), c.id


def test_ids_unique_across_files():
    seen = []
    root = Path(kb.__file__).parent / "kb"
    for f in root.glob("*.md"):
        seen += [c.id for c in kb.parse(f.read_text())]
    assert len(seen) == len(set(seen))


def test_doctor_cards_exist():
    cards = kb.load_all()
    src = Path(doctor.__file__).read_text()
    for card in re.findall(r'card="([^"]+)"', src):
        assert card in cards, card


def test_card_cross_references_resolve():
    cards = kb.load_all()
    code = "".join(p.read_text() for p in Path(kb.__file__).parent.glob("*.py"))
    for ref in re.findall(r"See ((?:linux|stats|method|startup|virt|build|gpu)\.[a-z-]+)", code):
        assert ref in cards, ref


def test_search_and_tags():
    assert kb.search("coordinated omission")[0].id == "latency.coordinated-omission"
    ids = {c.id for c in kb.search(tags=["rust"], limit=100)}
    assert "lang.rust" in ids and "lang.go" not in ids


def test_overlay(tmp_path):
    (tmp_path / "x.md").write_text("## acme.rack — Rack quirk\ntags: linux\nstatus: unverified\n\nPrivate note.\n\n## linux.swap — Replaced\ntags: linux\nstatus: unverified\n\nOurs.\n")
    cards = kb.load_all([str(tmp_path)])
    assert cards["acme.rack"].origin == "overlay"
    assert cards["linux.swap"].body == "Ours."


def test_env_var_overlay(tmp_path, monkeypatch):
    (tmp_path / "x.md").write_text("## acme.y — Y\ntags: linux\n\nBody.\n")
    monkeypatch.setenv("BENCHSANE_KB_PATH", str(tmp_path))
    assert "acme.y" in kb.load_all()
