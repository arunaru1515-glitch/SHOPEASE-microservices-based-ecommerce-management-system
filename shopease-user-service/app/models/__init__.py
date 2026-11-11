"""SQLAlchemy database models for User Service."""
from app.models.user_model import UserProfile
from app.models.address_model import UserAddress

__all__ = ["UserProfile", "UserAddress"]
