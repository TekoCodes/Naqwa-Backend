from fastapi import FastAPI
from routers import users
import uvicorn

app = FastAPI(title="My API")

app.include_router(users.router, prefix="/users")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
