from sqlalchemy import Column, BigInteger, String, Integer, SmallInteger
from models.base import Base


class MAIapikey(Base):
    __tablename__ = "maiapikey"

    apikeyid = Column("apikeyid", BigInteger, primary_key=True, index=True)
    apikey = Column("apikey", String(255), unique=True, nullable=False)
    userid = Column("userid", Integer, nullable=False)
    tenantid = Column("tenantid", Integer, nullable=False)
    botcode = Column("botcode", String(50), nullable=False)
    capabilitycode = Column("capabilitycode", String(50), nullable=False)
    status = Column("status", SmallInteger, default=1)
