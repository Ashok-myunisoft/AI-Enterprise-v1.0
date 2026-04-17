from sqlalchemy import Column, BigInteger, String, SmallInteger, Integer, Text
from models.base import Base

class MAIcapability(Base):
    __tablename__ = "maicapability"

    AIcapabilityid = Column("aicapabilityid",BigInteger, primary_key=True, index=True)
    AIcapabilitycode = Column("aicapabilitycode",String(50), unique=True, nullable=False)
    AIcapabilityname = Column("aicapabilityname",String(100), nullable=False)
    maxmaturitylevel = Column("maxmaturitylevel",SmallInteger)
    STATUS = Column("status",SmallInteger)
    TENANTID = Column("tenantid",Integer)
    keywords = Column("keywords", Text, nullable=True)



