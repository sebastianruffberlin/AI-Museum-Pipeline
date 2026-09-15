from __future__ import annotations

import json
from typing import Any, Optional

from ..persistence.postgres import PostgresStore, safe_ident


class RunState:
    """Persistent phase hand-off / resume state, separate from museum data."""
    def __init__(self, store: PostgresStore):
        self.store=store
        self.schema=safe_ident(store.cfg.settings.run_schema)

    def ensure(self,conn)->None:
        with self.store.cursor(conn) as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
            cur.execute(f'''CREATE TABLE IF NOT EXISTS {self.schema}.run_state (
                obj_id text NOT NULL, key text NOT NULL, value text, ts timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY(obj_id,key))''')
            cur.execute(f'''CREATE TABLE IF NOT EXISTS {self.schema}.run_errors (
                obj_id text NOT NULL, phase text NOT NULL, reason text, ts timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY(obj_id,phase))''')
        conn.commit()

    def set(self,conn,obj_id:str,key:str,value:Any)->None:
        text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
        with self.store.cursor(conn) as cur:
            cur.execute(f'''INSERT INTO {self.schema}.run_state(obj_id,key,value) VALUES(%s,%s,%s)
                ON CONFLICT(obj_id,key) DO UPDATE SET value=EXCLUDED.value,ts=now()''',(obj_id,key,text or ""))
        conn.commit()

    def get(self,conn,obj_id:str,key:str,*,required:bool=False)->Optional[str]:
        with self.store.cursor(conn) as cur:
            cur.execute(f"SELECT value FROM {self.schema}.run_state WHERE obj_id=%s AND key=%s",(obj_id,key)); row=cur.fetchone()
        value=row[0] if row else None
        if required and (value is None or not str(value).strip()): return None
        return value

    def get_json(self,conn,obj_id:str,key:str,*,required:bool=False)->Any:
        value=self.get(conn,obj_id,key,required=required)
        if value is None: return None
        try: return json.loads(value)
        except Exception: return None

    def has(self,conn,obj_id:str,key:str)->bool:
        with self.store.cursor(conn) as cur:
            cur.execute(f"SELECT 1 FROM {self.schema}.run_state WHERE obj_id=%s AND key=%s",(obj_id,key)); return cur.fetchone() is not None

    def failed(self,conn,obj_id:str)->bool:
        with self.store.cursor(conn) as cur:
            cur.execute(f"SELECT 1 FROM {self.schema}.run_errors WHERE obj_id=%s LIMIT 1",(obj_id,)); return cur.fetchone() is not None

    def fail(self,conn,obj_id:str,phase:str,reason:str)->None:
        with self.store.cursor(conn) as cur:
            cur.execute(f'''INSERT INTO {self.schema}.run_errors(obj_id,phase,reason) VALUES(%s,%s,%s)
                ON CONFLICT(obj_id,phase) DO UPDATE SET reason=EXCLUDED.reason,ts=now()''',(obj_id,phase,(reason or "")[:1000]))
        conn.commit()

    def clear_object(self,conn,obj_id:str)->None:
        with self.store.cursor(conn) as cur:
            cur.execute(f"DELETE FROM {self.schema}.run_state WHERE obj_id=%s",(obj_id,))
            cur.execute(f"DELETE FROM {self.schema}.run_errors WHERE obj_id=%s",(obj_id,))
        conn.commit()
