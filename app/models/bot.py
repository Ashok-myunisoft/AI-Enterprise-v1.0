from sqlalchemy import Column, BigInteger, String, SmallInteger, Integer
from models.base import Base

class MAIbot(Base):
    __tablename__ = "maibot"

    AIbotid = Column("aibotid",BigInteger, primary_key=True, index=True)
    AIbotcode = Column("aibotcode",String(50), unique=True, nullable=False)
    name = Column("name",String(150))
    AIinitiativeid = Column("aiinitiativeid",BigInteger)
    description = Column("description",String)
    isreadonly = Column("isreadonly",SmallInteger)
    STATUS = Column("status",SmallInteger)
    VERSION = Column("version",SmallInteger)
    TENANTID = Column("tenantid",Integer)
    