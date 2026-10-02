from sqlalchemy import BigInteger, Column, DateTime, Text, String
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class URL(Base):
    __tablename__ = "urls"

    id = Column(BigInteger,primary_key=True)
    short_code = Column(String(8),nullable=False,unique=True)
    original_url = Column(Text, nullable = False,unique=True)
    created_at = Column(DateTime(timezone=True),nullable=False,default=datetime.utcnow)
    last_clicked_at = Column(DateTime(timezone=True), nullable=True)
    click_count = Column(BigInteger,nullable=False,default=0)