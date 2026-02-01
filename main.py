from datetime import datetime, timedelta
from typing import Union
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi import Request


# --- CONFIGURATION ---
SECRET_KEY = "your_super_secret_key_here" # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# --- SECURITY UTILS ---
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- MOCK DATABASE ---
# In a real app, use SQL (PostgreSQL, SQLite) or NoSQL (MongoDB)
fake_users_db = {}

# --- PYDANTIC MODELS ---
class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserRegister(BaseModel):
    username: str
    password: str
    email: str | None = None

# --- HELPER FUNCTIONS ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- AUTH DEPENDENCY ---
# This function acts as a security gatekeeper for protected routes
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return UserInDB(**user)

# --- ENDPOINTS ---

@app.post("/register", status_code=201)
async def register_user(user: UserRegister):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    
    # Save to mock DB
    fake_users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "disabled": False
    }
    return {"message": "User registered successfully"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):

    print("USERNAME:", form_data.username)
    print("PASSWORD:", form_data.password)

    # OAuth2PasswordRequestForm automatically looks for 'username' and 'password' fields
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_dict["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    This endpoint is PROTECTED. 
    It requires a valid JWT token in the Authorization header.
    """
    return current_user

@app.get("/dashboard")
async def dashboard(current_user: User = Depends(get_current_user)):
    """
    Another example of a protected route.
    """
    return {"message": f"Welcome to the secret dashboard, {current_user.username}!"}