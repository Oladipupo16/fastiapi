from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name       = Column(String)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    listings         = relationship("Listing", back_populates="owner")
    listing_requests = relationship("ListingRequest", back_populates="owner")


class Agent(Base):
    __tablename__ = "agents"
    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String, nullable=False)
    company        = Column(String)
    phone          = Column(String)
    location       = Column(String)
    rating         = Column(Float, default=5.0)
    listings_count = Column(Integer, default=0)
    created_at     = Column(DateTime, default=datetime.utcnow)

    listings = relationship("Listing", back_populates="agent")


class Listing(Base):
    __tablename__ = "listings"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id    = Column(Integer, ForeignKey("agents.id"), nullable=True)
    title       = Column(String, nullable=False)
    purpose     = Column(String, nullable=False)
    category    = Column(String, nullable=False)
    location    = Column(String, nullable=False)
    price       = Column(Float, nullable=False)
    price_label = Column(String)
    description = Column(Text)
    image       = Column(String)
    status      = Column(String, default="active")
    created_at  = Column(DateTime, default=datetime.utcnow)

    owner     = relationship("User", back_populates="listings")
    agent     = relationship("Agent", back_populates="listings")
    enquiries = relationship("Enquiry", back_populates="listing")


class Enquiry(Base):
    __tablename__ = "enquiries"
    id         = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    name       = Column(String)
    contact    = Column(String)
    message    = Column(Text)
    status     = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="enquiries")


class ListingRequest(Base):
    __tablename__ = "listing_requests"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    title      = Column(String, nullable=False)
    type       = Column(String)
    location   = Column(String)
    price      = Column(String)
    details    = Column(Text)
    status     = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="listing_requests")