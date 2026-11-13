from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class Product(Base):
    """
    SQLAlchemy Product model representing catalog products.
    Mapped to table 'products'.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    discount_price = Column(Numeric(10, 2), nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    image_url = Column(String(500), nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="chk_positive_price"),
        CheckConstraint("stock_quantity >= 0", name="chk_non_negative_stock"),
    )

    # Relationships
    category = relationship("Category", back_populates="products")
    inventory_transactions = relationship(
        "InventoryTransaction",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="desc(InventoryTransaction.created_at)",
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}', price={self.price}, stock={self.stock_quantity})>"

