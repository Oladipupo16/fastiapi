from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import models
from database import engine, get_db
from auth import hash_password, verify_password, create_access_token, get_current_user_id

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ✅ Allow your frontend to talk to your backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic Schemas ──────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class ListingCreate(BaseModel):
    title: str
    purpose: str
    category: str
    location: str
    price: float
    price_label: str
    description: str
    image: Optional[str] = "assets/house.svg"
    agent_id: Optional[int] = None

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    purpose: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    price: Optional[float] = None
    price_label: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class EnquiryCreate(BaseModel):
    listing_id: int
    name: Optional[str] = "Website visitor"
    contact: Optional[str] = None
    message: Optional[str] = None

class ListingRequestCreate(BaseModel):
    title: str
    type: str
    location: str
    price: str
    details: str

class AgentCreate(BaseModel):
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    rating: Optional[float] = 5.0

# ── Auth Routes ───────────────────────────────────────────────────

@app.post("/auth/signup", status_code=201)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = models.User(
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created!", "user_id": new_user.id}

@app.post("/auth/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(data={"user_id": db_user.id})
    return {"access_token": token, "token_type": "bearer"}

# ── Listings Routes ───────────────────────────────────────────────

@app.get("/api/listings")
def list_listings(
    purpose: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    maxPrice: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Listing).filter(models.Listing.status == "active")
    if purpose and purpose != "all":
        query = query.filter(models.Listing.purpose == purpose)
    if category and category != "all":
        query = query.filter(models.Listing.category == category)
    if location and location != "all":
        query = query.filter(models.Listing.location == location)
    if maxPrice:
        query = query.filter(models.Listing.price <= maxPrice)
    return {"listings": query.all()}

@app.get("/api/listings/{listing_id}")
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(models.Listing).filter(
        models.Listing.id == listing_id,
        models.Listing.status == "active"
    ).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"listing": listing}

@app.post("/api/listings", status_code=201)
def create_listing(
    listing: ListingCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    db_listing = models.Listing(**listing.dict(), user_id=current_user_id)
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return {"listing": db_listing}

@app.put("/api/listings/{listing_id}")
def update_listing(
    listing_id: int,
    listing: ListingUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    db_listing = db.query(models.Listing).filter(
        models.Listing.id == listing_id,
        models.Listing.user_id == current_user_id
    ).first()
    if not db_listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    for field, value in listing.dict(exclude_none=True).items():
        setattr(db_listing, field, value)
    db.commit()
    db.refresh(db_listing)
    return {"listing": db_listing}

@app.delete("/api/listings/{listing_id}", status_code=204)
def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    db_listing = db.query(models.Listing).filter(
        models.Listing.id == listing_id,
        models.Listing.user_id == current_user_id
    ).first()
    if not db_listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    db_listing.status = "archived"
    db.commit()
    return

# ── Enquiries Routes ──────────────────────────────────────────────

@app.post("/api/enquiries", status_code=201)
def create_enquiry(enquiry: EnquiryCreate, db: Session = Depends(get_db)):
    listing = db.query(models.Listing).filter(
        models.Listing.id == enquiry.listing_id,
        models.Listing.status == "active"
    ).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    db_enquiry = models.Enquiry(**enquiry.dict())
    db.add(db_enquiry)
    db.commit()
    db.refresh(db_enquiry)
    return {"enquiry": db_enquiry}

@app.get("/api/enquiries")
def list_enquiries(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return {"enquiries": db.query(models.Enquiry).all()}

# ── Listing Requests Routes ───────────────────────────────────────

@app.post("/api/listing-requests", status_code=201)
def create_listing_request(
    request: ListingRequestCreate,
    db: Session = Depends(get_db)
):
    db_request = models.ListingRequest(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return {"request": db_request}

@app.get("/api/listing-requests")
def list_requests(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return {"requests": db.query(models.ListingRequest).all()}

# ── Agents Routes ─────────────────────────────────────────────────

@app.get("/api/agents")
def list_agents(db: Session = Depends(get_db)):
    return {"agents": db.query(models.Agent).all()}

@app.post("/api/agents", status_code=201)
def create_agent(
    agent: AgentCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    db_agent = models.Agent(**agent.dict())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return {"agent": db_agent}

# ── Health Check ──────────────────────────────────────────────────

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    return {
        "ok": True,
        "listings": db.query(models.Listing).count(),
        "enquiries": db.query(models.Enquiry).count(),
        "agents": db.query(models.Agent).count(),
    }