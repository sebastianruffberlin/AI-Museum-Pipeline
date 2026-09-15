from pathlib import Path
from types import SimpleNamespace
import json
import pytest

from museum_pipeline.domain.topics import TopicsModule

ROOT = Path(__file__).resolve().parents[1]


class Store:
    def __init__(self, row): self.row = row
    def query_profile_resource(self, conn, path): return self.row


def module(tmp_path, resources, row):
    (tmp_path / "topics").mkdir()
    cfg = SimpleNamespace(museum=SimpleNamespace(root=tmp_path, topics={"resources": resources}))
    return TopicsModule(cfg, Store(row), None)


def test_database_topics_can_use_explicit_file_fallback(tmp_path):
    (tmp_path / "topics").mkdir()
    (tmp_path / "topics" / "framework.md").write_text("FRAMEWORK", encoding="utf-8")
    (tmp_path / "topics" / "taxonomy.json").write_text(json.dumps({"topics":[{"label":"Demo","slug":"demo"}]}), encoding="utf-8")
    cfg = SimpleNamespace(museum=SimpleNamespace(root=tmp_path, topics={"resources": {
        "source":"database", "database_query":"query.sql",
        "framework_fallback":"framework.md", "taxonomy_fallback":"taxonomy.json"}}))
    m = TopicsModule(cfg, Store({"framework":"", "taxonomy":[]}), None)
    framework, taxonomy, slugs = m.resources(None)
    assert framework == "FRAMEWORK"
    assert json.loads(taxonomy)["topics"][0]["label"] == "Demo"
    assert slugs["Demo"] == "demo"


def test_empty_database_topics_without_fallback_has_actionable_error(tmp_path):
    (tmp_path / "topics").mkdir()
    cfg = SimpleNamespace(museum=SimpleNamespace(root=tmp_path, topics={"resources": {
        "source":"database", "database_query":"query.sql"}}))
    m = TopicsModule(cfg, Store({"framework":"", "taxonomy":[]}), None)
    with pytest.raises(RuntimeError, match="no file fallback"):
        m.resources(None)
