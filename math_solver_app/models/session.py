from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime

from math_solver_app.db.database import Base


class Session(Base):
    __tablename__ = "session"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
