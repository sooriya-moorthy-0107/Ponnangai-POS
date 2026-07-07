from datetime import datetime, date, time
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False) # Admin, Owner, Manager, Shopkeeper, Factory
    is_deleted = Column(Boolean, default=False)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    image_filename = Column(String, nullable=True)
    shopkeeper_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    product_type = Column(String, default="solid") # "solid" or "liquid"
    unit = Column(String, default="Pcs") # "Pcs", "Liters", etc.
    rate_qty = Column(Float, nullable=True)

    shopkeeper = relationship("User")

class ShopInventory(Base):
    __tablename__ = "shop_inventories"
    id = Column(Integer, primary_key=True, index=True)
    shopkeeper_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    stock = Column(Integer, default=0)

    shopkeeper = relationship("User")
    product = relationship("Product")

class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    final_amount = Column(Float, nullable=False)
    round_off = Column(Float, default=0.0)
    payment_mode = Column(String, default="Cash") # Cash/UPI
    timestamp = Column(DateTime, default=datetime.now)
    cashier_id = Column(Integer, ForeignKey("users.id"))
    cashier_name = Column(String, nullable=True)
    is_cancelled = Column(Boolean, default=False)

    cashier = relationship("User")
    items = relationship("BillItem", back_populates="bill")

class BillItem(Base):
    __tablename__ = "bill_items"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, nullable=False) # Changed from Integer to Float for loose quantity sales
    price_at_sale = Column(Float, nullable=False)
    packaging_type = Column(String, default="loose") # loose, bottle
    bottle_type = Column(String, nullable=True) # Pharma Bottle, Lotus Bottle, etc.
    bottle_count = Column(Integer, default=0)

    bill = relationship("Bill", back_populates="items")
    product = relationship("Product")

class CashTransaction(Base):
    __tablename__ = "cash_transactions"
    id = Column(Integer, primary_key=True, index=True)
    shopkeeper_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False) # "IN" or "OUT"
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

    shopkeeper = relationship("User")

