from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from app.routers import session, question, answer, result, stt, tts, admin
from app.repositories.result_repository import init_csv
from core.config import STATIC_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_csv()
        from app.services.stt_service import preload_model  # temp

        preload_model()
    except Exception as e:
        # print(f"Startup Error: {e}")
        raise e
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router, prefix="/session", tags=["Session"])
app.include_router(question.router, prefix="/question", tags=["Survey"])
app.include_router(answer.router, prefix="/answer", tags=["Answer"])
app.include_router(result.router, prefix="/result", tags=["Data"])
app.include_router(stt.router, prefix="/stt", tags=["Utility"])
app.include_router(tts.router, prefix="/tts", tags=["Utility"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}
