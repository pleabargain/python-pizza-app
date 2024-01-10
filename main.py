# Import necessary libraries and modules
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import pydantic
from pydantic import Field, constr


# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./pizza.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ORM models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Pizza(Base):
    __tablename__ = 'pizzas'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    size = Column(String)
    topping = Column(String)
    price = Column(Float)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    pizza_id = Column(Integer)

# Pydantic schemas
class UserSchema(pydantic.BaseModel):
    name: str

class PizzaSchema(pydantic.BaseModel):
    name: str
    size: str = Field(..., pattern="^(small|medium|large)$")  # Only allow "small", "medium", or "large"
    topping: str = Field(..., pattern="^(pepperoni|mushrooms|onions|sausage|bacon)$")  # Only allow these 5 toppings
    price: float = Field(..., gt=10.0)  # Set a minimum price of 10.0

class OrderSchema(pydantic.BaseModel):
    user_id: int
    pizza_id: int

# FastAPI app setup
app = FastAPI()

# Database utility functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API endpoints
@app.post("/register", response_model=UserSchema)
def register_user(user_details: UserSchema, db: Session = Depends(get_db)):
    """
    Register a new user.

    This endpoint accepts a JSON body with the user's details and creates a new user in the database.

    Args:
        user_details (UserSchema): The user's details.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        UserSchema: The created user's details.
    """
    existing_user = db.query(User).filter(User.name == user_details.name).first()
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="User with this name already exists. Please use a different name.")
    new_user = User(name=user_details.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/order", response_model=OrderSchema)
def place_order(order_details: OrderSchema, db: Session = Depends(get_db)):
    """
    Place a new order.

    This endpoint accepts a JSON body with the order details and creates a new order in the database.

    Args:
        order_details (OrderSchema): The order details.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        OrderSchema: The created order's details.
    """
    # Check if the user exists
    user = db.query(User).filter(User.id == order_details.user_id).first()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found.")

    # Check if the pizza exists
    pizza = db.query(Pizza).filter(Pizza.id == order_details.pizza_id).first()
    if pizza is None:
        raise HTTPException(status_code=400, detail="Pizza not found.")

    # Create the new order
    new_order = Order(user_id=order_details.user_id, pizza_id=order_details.pizza_id)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

# Create the database tables
Base.metadata.create_all(bind=engine)

# Application entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)