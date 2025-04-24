from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, String

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id_telegram: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gender: Mapped[str] = mapped_column(String(1))
    age: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column()
    height: Mapped[float] = mapped_column()
