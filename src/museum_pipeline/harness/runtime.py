from __future__ import annotations

import threading

from ..configuration import RuntimeConfig
from ..infrastructure.assets import AssetClient
from ..infrastructure.llm import LLMClient
from ..persistence.context import ContextBuilder
from ..persistence.postgres import PostgresStore
from ..domain.tagging import TaggingModule
from ..domain.emotion import EmotionModule
from ..domain.topics import TopicsModule
from ..skills.loader import SkillLoader
from .state import RunState


class ConnectionPool:
    def __init__(self, store: PostgresStore):
        self.store=store; self.local=threading.local(); self.all=[]; self.lock=threading.Lock()
    def get(self):
        conn=getattr(self.local,"conn",None)
        if conn is None or getattr(conn,"closed",False):
            conn=self.store.connect(); self.local.conn=conn
            with self.lock: self.all.append(conn)
        return conn
    def close_all(self):
        with self.lock:
            for conn in self.all:
                try: conn.close()
                except Exception: pass
            self.all.clear()
        self.local=threading.local()


class ImageCache:
    def __init__(self, assets: AssetClient):
        self.assets=assets; self.cache={}; self.lock=threading.Lock()
    def get(self,obj_id:str,asset_ref:dict):
        with self.lock:
            if obj_id in self.cache: return self.cache[obj_id]
        value=self.assets.load_image(obj_id,asset_ref)
        with self.lock:
            self.cache.setdefault(obj_id,value)
            return self.cache[obj_id]


class Runtime:
    def __init__(self,cfg:RuntimeConfig):
        self.cfg=cfg
        self.store=PostgresStore(cfg)
        self.context=ContextBuilder(cfg,self.store)
        self.assets=AssetClient(cfg)
        self.llm=LLMClient(cfg)
        self.state=RunState(self.store)
        self.skills=SkillLoader(cfg)
        self.pool=ConnectionPool(self.store)
        self.images=ImageCache(self.assets)
        self.tagging=TaggingModule(cfg,self.store,self.llm)
        self.emotion=EmotionModule(cfg,self.store,self.llm)
        self.topics=TopicsModule(cfg,self.store,self.llm)

    def initialize(self):
        conn=self.pool.get(); self.state.ensure(conn); self.pool.close_all()
