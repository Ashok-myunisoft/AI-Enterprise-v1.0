from sqlalchemy import Column, BigInteger, String, SmallInteger, Integer
from models.base import Base

class MAIinitiative(Base):
    __tablename__ = "maiinitiative"

    aiinitiativeid = Column("aiinitiativeid", BigInteger, primary_key=True, index=True)
    aiinitiativecode = Column("aiinitiativecode", String(50), unique=True, nullable=False)
    aiinitiativename = Column("aiinitiativename", String(150), nullable=False)
    maturitylevel = Column("maturitylevel", SmallInteger)
    status = Column("status", SmallInteger)
    tenantid = Column("tenantid", Integer)