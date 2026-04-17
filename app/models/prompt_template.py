from sqlalchemy import Column, BigInteger, String, SmallInteger, Integer, Text
from models.base import Base


class MAIprompttemplate(Base):
    __tablename__ = "maiprompttemplate"

    aipromptid = Column("aipromptid", BigInteger, primary_key=True, index=True)
    initiativecode = Column("initiativecode", String(100), nullable=False)
    capabilitycode = Column("capabilitycode", String(100), nullable=False)
    tenantid = Column("tenantid", Integer, nullable=False)
    prompttemplate = Column("prompttemplate", Text, nullable=False)
    version = Column("version", Integer, default=1)
    status = Column("status", SmallInteger, default=1)
