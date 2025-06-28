from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id_telegram: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gender: Mapped[str] = mapped_column(String(1))
    age: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column()
    height: Mapped[float] = mapped_column()

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    cal_per_100g: Mapped[float] = mapped_column()

class FoodEntry(Base):
    __tablename__ = "food_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id_telegram"))
    calories: Mapped[float] = mapped_column()
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
