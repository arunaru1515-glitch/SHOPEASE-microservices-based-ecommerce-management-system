from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class UserAddress(Base):
    """
    SQLAlchemy UserAddress model representing delivery addresses.
    Mapped to table 'user_addresses'.
    Foreign key references 'user_profiles.id'.
    """
    __tablename__ = "user_addresses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    address_type = Column(String(50), nullable=False, default="Home")
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationship back to UserProfile
    user_profile = relationship("UserProfile", back_populates="addresses")

    def __repr__(self) -> str:
        return f"<UserAddress(id={self.id}, user_id={self.user_id}, city='{self.city}', is_default={self.is_default})>"

