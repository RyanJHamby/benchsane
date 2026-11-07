import csv
import io
import json
from importlib import resources

import jsonschema

from benchsane import cli, formats
from benchsane.ab import run_ab
from benchsane.capture import capture
from benchsane.compare import compare
from benchsane.doctor import report, run_checks
import sys

CMD = f"{sys.executable} -c 'pass'"


def schema(name):
    return json.loads((resources.files("benchsane") / "schemas" / f"{name}.schema.json").read_text())


def validate(obj, name):
    jsonschema.Draft202012Validator.check_schema(schema(name))
    jsonschema.validate(obj, schema(name), format_checker=jsonschema.FormatChecker())


def make(tmp_path):
    out = tmp_path / "r"
    r, env = run_ab(CMD, CMD, runs=3, warmup=0, seed=1, out=str(out))
    return r, env, out


def test_all_outputs_match_their_schemas(tmp_path):
    r, env, out = make(tmp_path)
    validate(json.loads((out / "samples.json").read_text()), "result")
    validate(json.loads((out / "env.json").read_text()), "env")
    validate(report(run_checks()), "doctor")
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("1 1.1 1.2")
    b.write_text("1 1.1 1.2")
    validate(compare(str(a), str(b)), "comparison")


def test_every_sample_uses_declared_metrics(tmp_path):
    r, _, _ = make(tmp_path)
    for rows in r["samples"].values():
        for s in rows:
            assert set(s) - {"block", "env_pad"} == set(formats.METRICS)


def test_units_are_ucum_and_names_carry_no_unit():
    for name, m in formats.METRICS.items():
        assert m["unit"] in ("s", "By") or m["unit"].startswith("{")
        assert not name.endswith(("_s", "_ms", "_bytes", "_kib"))


def test_csv_is_tidy(tmp_path):
    r, _, _ = make(tmp_path)
    rows = list(csv.DictReader(io.StringIO(formats.to_csv(r))))
    assert len(rows) == 2 * 3 * len(formats.METRICS)
    assert set(rows[0]) == {"arm", "block", "env_pad_bytes", "metric", "value", "unit"}


def test_bmf_shape(tmp_path):
    r, _, _ = make(tmp_path)
    bmf = formats.to_bmf(r, "demo")
    m = bmf["demo/A"]["wall-time-seconds"]
    assert m["lower_value"] <= m["value"] <= m["upper_value"]


def test_github_benchmark_shape(tmp_path):
    r, _, _ = make(tmp_path)
    for row in formats.to_github_benchmark(r):
        assert {"name", "unit", "value"} <= set(row) and isinstance(row["range"], str)


def test_claim_carries_evidence():
    c = formats.comparison_record({"ratio": 1.1, "lo": 1.05, "hi": 1.15, "level": 0.95, "paired": True}, "slower", 30, 30, 0.01)
    env = capture()
    text = formats.claim(c, env)
    for part in ("10.0% slower", "95% CI", "n=30/30", "host grade", env["captured_at"][:10]):
        assert part in text


def test_timestamps_are_utc():
    assert formats.now().endswith("Z")


def test_export_cli(tmp_path, capsys):
    _, _, out = make(tmp_path)
    f = str(out / "samples.json")
    for to in ("csv", "bmf", "github-benchmark", "claim"):
        assert cli.main(["export", f, "--to", to]) == 0
    other = tmp_path / "x.json"
    other.write_text("{}")
    assert cli.main(["export", str(other), "--to", "csv"]) == 2
    assert cli.main(["schema", "result"]) == 0
