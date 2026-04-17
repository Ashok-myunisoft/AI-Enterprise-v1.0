from sqlalchemy import Column, BigInteger, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB
from models.base import Base

class TAIexecution(Base):
    __tablename__ = "taiexecution"

    AIexecutionid = Column("aiexecutionid",BigInteger, primary_key=True, index=True)
    userid = Column("userid",Integer)
    tenantid = Column("tenantid",Integer)
    AIinitiativeid = Column("aiinitiativeid",BigInteger)
    AIbotid = Column("aibotid",BigInteger)
    AIcapabilityid = Column("aicapabilityid",BigInteger)
    outcomestatus = Column("outcomestatus", SmallInteger)
    inputpayload = Column("inputpayload", JSONB)
    outputpayload = Column("outputpayload", JSONB)
    sessionid = Column("sessionid", String(255))