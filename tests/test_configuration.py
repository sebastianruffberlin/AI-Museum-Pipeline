from __future__ import annotations

import os
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('PG_HOST','test')
os.environ.setdefault('PG_DB','test')
os.environ.setdefault('PG_USER','test')
os.environ.setdefault('PG_PASSWORD','test')
os.environ.setdefault('LCPP_AUTH','test')
os.environ['MUSEUM_PIPELINE_HOME']=str(ROOT)

from museum_pipeline.settings import Settings
from museum_pipeline.configuration import RuntimeConfig


class ConfigurationTests(unittest.TestCase):
    def test_reference_profiles_load(self):
        cfg=RuntimeConfig.load(Settings.from_env(), "core-emotion")
        self.assertEqual(cfg.museum.data['id'],'stadtmuseum-berlin')
        self.assertEqual(cfg.hardware.data['status'],'verified')
        self.assertTrue(cfg.workflow.enabled('emotion'))
        self.assertFalse(cfg.workflow.enabled('topics'))

    def test_core_has_no_optional_semantic_modules(self):
        cfg=RuntimeConfig.load(Settings.from_env(), 'core')
        self.assertFalse(cfg.workflow.enabled('emotion'))
        self.assertFalse(cfg.workflow.enabled('topics'))


    def test_topics_workflow_requires_institution_configuration(self):
        with self.assertRaisesRegex(RuntimeError, "no topics configuration"):
            RuntimeConfig.load(Settings.from_env(), "core-topics")

    def test_hardware_roles_resolve(self):
        cfg=RuntimeConfig.load(Settings.from_env())
        for role in ['caption.primary','tagging.generator','emotion.generator','topics.generator']:
            self.assertGreaterEqual(cfg.hardware.workers_for_role(cfg.models,role),1)


if __name__=='__main__': unittest.main()
