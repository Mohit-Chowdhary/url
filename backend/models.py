from sqlalchemy import BigInteger, Column, DateTime, Text, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class URL(Base):
    __table_name__ = "urls"

    id = Column(BigInteger,primary_key=True)
    short_code = Column(String(8),nullable=False)
    original_url = Column(Text, nullable = False)
    created_at = Column(DateTime(timezone=True),nullable=False)
    last_clicked_at = Column(DateTime(timezone=True))
    click_count = Column(BigInteger,nullable=False)