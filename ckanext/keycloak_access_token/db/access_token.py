# encoding: utf-8
from __future__ import annotations

import datetime

from sqlalchemy import types, Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional


from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AccessTokenTable(Base):
    __tablename__ = 'access_token'

    def __init__(self, id, name, user_id, created_at, expires_at, last_access, plugin_extras):
        self.id = id
        self.name = name
        self.user_id = user_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_access = last_access
        self.plugin_extras = plugin_extras
        
   
    id = Column(types.UnicodeText, primary_key=True)
    name = Column(types.UnicodeText)
    user_id = Column(types.UnicodeText)
    created_at = Column(types.DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(types.DateTime)
    expires_in = Column(types.Integer)
    last_access = Column(types.DateTime, nullable=True)
    plugin_extras = Column(MutableDict.as_mutable(JSONB))
