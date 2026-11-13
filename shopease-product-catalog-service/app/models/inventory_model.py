from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class InventoryTransaction(Base):
    """
    SQLAlchemy InventoryTransaction model representing stock audit logs.
    Mapped to table 'inventory_transactions'.
    """
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type = Column(String(20), nullable=False)  # "IN" or "OUT"
    quantity = Column(Integer, nullable=False)
    previous_stock = Column(Integer, nullable=False)
    updated_stock = Column(Integer, nullable=False)
    remarks = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationship
    product = relationship("Product", back_populates="inventory_transactions")

    def __repr__(self) -> str:
        return (
            f"<InventoryTransaction(id={self.id}, product_id={self.product_id}, "
            f"type='{self.transaction_type}', qty={self.quantity}, "
            f"prev={self.previous_stock}, updated={self.updated_stock})>"
        )

