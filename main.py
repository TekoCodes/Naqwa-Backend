from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import login, register, forgot_password, admin_register, subjects, auth, dashboard, admin_crud, student_profile, site_status
import uvicorn

app = FastAPI(title="My API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://naqwaeg.com",
        "https://www.naqwaeg.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login.router, prefix="/api/v1")
app.include_router(register.router, prefix="/api/v1")
app.include_router(forgot_password.router, prefix="/api/v1")
app.include_router(admin_register.router, prefix="/api/v1")
app.include_router(subjects.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(admin_crud.router, prefix="/api/v1")
app.include_router(student_profile.router, prefix="/api/v1")
app.include_router(site_status.router, prefix="/api/v1")
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
