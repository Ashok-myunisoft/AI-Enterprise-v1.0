from sqlalchemy import Column, BigInteger, String, Integer, Text, SmallInteger
from models.base import Base


class MAImodel(Base):
    __tablename__ = "maimodel"

    AIModelid = Column("aimodelid", BigInteger, primary_key=True, index=True)

    modelcode = Column("modelcode", String(100), nullable=False)

    modelname = Column("modelname", String(100), nullable=False)

    provider = Column("provider", String(50), nullable=False)

    endpoint = Column("endpoint", Text, nullable=True)

    apikey = Column("apikey", Text, nullable=True)

    status = Column("status", SmallInteger, default=1)

    tenantid = Column("tenantid", Integer, nullable=False)

