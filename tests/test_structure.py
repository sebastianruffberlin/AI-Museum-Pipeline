from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

import yaml

ROOT=Path(__file__).resolve().parents[1]


class StructureTests(unittest.TestCase):
    def test_workflow_optional_modules(self):
        core=yaml.safe_load((ROOT/'workflows/core.yaml').read_text())['modules']
        emo=yaml.safe_load((ROOT/'workflows/core-emotion.yaml').read_text())['modules']
        topics=yaml.safe_load((ROOT/'workflows/core-topics.yaml').read_text())['modules']
        full=yaml.safe_load((ROOT/'workflows/full.yaml').read_text())['modules']
        self.assertFalse(core['emotion']); self.assertFalse(core['topics'])
        self.assertTrue(emo['emotion']); self.assertFalse(emo['topics'])
        self.assertFalse(topics['emotion']); self.assertTrue(topics['topics'])
        self.assertTrue(full['emotion']); self.assertTrue(full['topics'])

    def test_topics_are_engine_plus_institution_blueprint(self):
        topic_dir=ROOT/'profiles/_template/topics'
        self.assertTrue((topic_dir/'framework.template.md').exists())
        self.assertTrue((topic_dir/'taxonomy.template.json').exists())
        self.assertFalse((ROOT/'profiles/stadtmuseum-berlin/topics').exists())

    def test_reference_emotion_resources(self):
        all_concepts=json.loads((ROOT/'profiles/stadtmuseum-berlin/emotion/concepts.json').read_text())
        runtime=json.loads((ROOT/'profiles/stadtmuseum-berlin/emotion/vocabulary.runtime.json').read_text())
        self.assertEqual(len(all_concepts),146)
        self.assertEqual(len(runtime),121)
        self.assertTrue({'concept_id','begriff','definition'}.issubset(runtime[0]))

    def test_no_institution_semantics_in_src(self):
        forbidden=['Stadtmuseum Berlin','Stadtökologie','Geteilte Stadt','Nationalsozialismus','sammlungsbereich','objektbezeichnung','Thema_Phänomen','Emotion_Atmosphäre']
        text='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in (ROOT/'src').rglob('*.py'))
        for term in forbidden:
            self.assertNotIn(term,text,term)

    def test_reference_hardware_context_capacity(self):
        hw=yaml.safe_load((ROOT/'hardware/h100-80gb.yaml').read_text())
        self.assertEqual(hw['status'],'verified')
        for model,cfg in hw['models'].items():
            self.assertGreaterEqual(int(cfg['context_pool']),int(cfg['parallel_slots'])*int(cfg['min_context_per_slot']),model)

    def test_skill_contracts_exist(self):
        names=['caption-observation','caption-synthesis','keyword-generation','keyword-audit','keyword-repair','authority-gnd','emotion-generation','emotion-judge','topic-generation','topic-judge']
        for name in names:
            self.assertTrue((ROOT/'src/museum_pipeline/skills'/name/'SKILL.md').exists(),name)


if __name__=='__main__': unittest.main()
