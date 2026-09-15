from __future__ import annotations

from museum_pipeline.domain.authority.gnd import GNDAuthority


class _FakeLLM:
    def __init__(self):
        self.calls=[]
    def chat_content(self, role, body):
        self.calls.append((role,body))
        return '{"gnd_id": null, "gnd_confidence": "no_match"}'


def test_gnd_adapter_calls_llm_with_role_and_body():
    g=GNDAuthority.__new__(GNDAuthority)
    g.profile={"role":"authority.gnd"}
    g.llm=_FakeLLM()
    g._body=lambda term,candidates: {"messages":[],"term":term["term"]}
    out=g._call_one({"term":"Straße","cluster":"theme"},[])
    assert g.llm.calls == [("authority.gnd",{"messages":[],"term":"Straße"})]
    assert out["final_response"]
