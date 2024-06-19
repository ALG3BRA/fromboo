from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.handlers import user_router
from api.login_handler import login_router

app = FastAPI(title="fromboo")
main_api_router = APIRouter()

main_api_router.include_router(user_router, prefix="/user")
main_api_router.include_router(login_router, prefix="/login")
app.include_router(main_api_router)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8000/login/token",
    "http://localhost:8000/login/refresh",
    "http://127.0.0.1:8000/login/refresh",
    "chrome-extension://gnkoiigiddipdiienojahafkapllelcp"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
