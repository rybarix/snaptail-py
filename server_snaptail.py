import importlib.util
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Example of how server_user.py should look like:
"""
from fastapi import FastAPI

router = FastAPI()

@router.get("/")
async def root():
    return {"message": "Hello World"}

@router.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@router.post("/users")
async def create_user(name: str):
    return {"name": name}
"""

def import_user_routes(file_path):
    spec = importlib.util.spec_from_file_location("user_routes", file_path)
    user_routes = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_routes)
    print(user_routes)
    return user_routes

def bind_routes_to_app(app, user_routes):
    if hasattr(user_routes, 'router'):
        print("hello!")
        print(user_routes.router)
        app.include_router(user_routes.router, prefix="")
    else:
        print("Warning: 'router' not found in user_routes. No routes will be added.")

# Assuming the user's file is named 'server_user.py' in the same directory
user_file_path = os.path.join(os.path.dirname(__file__), 'api.py')

if os.path.exists(user_file_path):
    user_routes = import_user_routes(user_file_path)
    bind_routes_to_app(app, user_routes)
else:
    print(f"Warning: {user_file_path} not found. No user-defined routes will be added.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
