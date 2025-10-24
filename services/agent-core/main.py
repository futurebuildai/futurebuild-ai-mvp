import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, firestore
from sqlalchemy import create_engine, text

# --- Firebase Admin SDK Setup ---
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()

# --- Database Clients ---
# Initialize both our database clients
db = firestore.client()  # Firestore client
try:
    # We read these from environment variables set by Cloud Run
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST") # This will be the Private IP: 10.48.0.2
    DB_NAME = os.getenv("DB_NAME") # This will be futurebuild_projects

    if not all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
        raise RuntimeError("Missing one or more database environment variables")

    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(DATABASE_URL) # Cloud SQL client
except Exception as e:
    print(f"FATAL: Could not create database engine: {e}")
    raise

# --- FastAPI Application ---
app = FastAPI()
token_auth_scheme = HTTPBearer()

# --- Authentication Dependency ---
async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    """
    FastAPI dependency to verify Firebase ID token.
    """
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        decoded_token = auth.verify_id_token(creds.credentials)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decoded_token

# --- API Endpoints ---
@app.get("/")
def read_root(user: dict = Depends(get_current_user)):
    """
    A secure root endpoint that returns the authenticated user's UID.
    """
    uid = user.get("uid")
    return {"hello": f"authenticated user with UID: {uid}"}


@app.get("/projects")
def get_projects(user: dict = Depends(get_current_user)):
    """
    A secure endpoint to fetch all projects for the user's organization.
    This is a "hybrid query" that uses both Firestore and Cloud SQL.
    """
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not found in token")

    organization_id = None
    try:
        # 1. Query Firestore to find the user's organization_id
        # We query the 'users' collection group to find a doc with this user's email
        user_docs_query = db.collection_group('users').where('email', '==', email).limit(1).stream()
        user_doc = next(iter(user_docs_query), None)
        
        if not user_doc:
            raise HTTPException(status_code=404, detail="User organization not found in Firestore.")
        
        # Get the 'organization_id' by getting the parent's parent ID
        organization_id = user_doc.reference.parent.parent.id

    except Exception as e:
        print(f"Firestore query failed: {e}")
        raise HTTPException(status_code=503, detail="Could not fetch user organization from Firestore.")

    if not organization_id:
        raise HTTPException(status_code=404, detail="Organization ID not found for user.")

    try:
        # 2. Use the organization_id to query the Cloud SQL database
        sql_query = text("SELECT * FROM projects WHERE organization_id = :org_id")
        
        with engine.connect() as connection:
            result = connection.execute(sql_query, {"org_id": organization_id})
            # .mappings().all() converts the SQL result into a clean list of dicts
            projects = result.mappings().all()
            return projects
            
    except Exception as e:
        print(f"Cloud SQL query failed: {e}")
        raise HTTPException(status_code=503, detail="Could not fetch projects from Cloud SQL.")