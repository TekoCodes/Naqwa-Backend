from fastapi import FastAPI
from routers import login, register, forgot_password, admin_register, subjects
import uvicorn

app = FastAPI(title="My API")

app.include_router(login.router, prefix="/api/v1")
app.include_router(register.router, prefix="/api/v1")
app.include_router(forgot_password.router, prefix="/api/v1")
app.include_router(admin_register.router, prefix="/api/v1")
app.include_router(subjects.router, prefix="/api/v1")
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
