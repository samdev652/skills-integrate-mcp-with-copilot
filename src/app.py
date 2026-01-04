"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
import json
import secrets
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Session management - stores active sessions
active_sessions = {}

# Load teacher credentials from JSON file
def load_teachers():
    teachers_file = Path(__file__).parent / "teachers.json"
    with open(teachers_file, 'r') as f:
        data = json.load(f)
    return {teacher['username']: teacher['password'] for teacher in data['teachers']}

teachers = load_teachers()

# Pydantic models for request bodies
class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    email: str

class UnregisterRequest(BaseModel):
    email: str

# Helper function to check if user is authenticated
def is_authenticated(request: Request) -> bool:
    session_token = request.cookies.get("session_token")
    return session_token in active_sessions

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/login")
def login(login_data: LoginRequest, response: Response):
    """Authenticate a teacher and create a session"""
    username = login_data.username
    password = login_data.password
    
    # Check credentials
    if username in teachers and teachers[username] == password:
        # Create session token
        session_token = secrets.token_hex(16)
        active_sessions[session_token] = username
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=3600  # 1 hour
        )
        return {"message": "Login successful", "username": username}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/logout")
def logout(request: Request, response: Response):
    """Log out a teacher and destroy the session"""
    session_token = request.cookies.get("session_token")
    if session_token in active_sessions:
        del active_sessions[session_token]
    
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}


@app.get("/auth/status")
def auth_status(request: Request):
    """Check if user is authenticated"""
    if is_authenticated(request):
        session_token = request.cookies.get("session_token")
        username = active_sessions[session_token]
        return {"authenticated": True, "username": username}
    return {"authenticated": False}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, signup_data: SignupRequest, request: Request):
    """Sign up a student for an activity (requires authentication)"""
    # Check authentication
    if not is_authenticated(request):
        raise HTTPException(status_code=403, detail="Authentication required. Only teachers can register students.")
    
    email = signup_data.email
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, unregister_data: UnregisterRequest, request: Request):
    """Unregister a student from an activity (requires authentication)"""
    # Check authentication
    if not is_authenticated(request):
        raise HTTPException(status_code=403, detail="Authentication required. Only teachers can unregister students.")
    
    email = unregister_data.email
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
