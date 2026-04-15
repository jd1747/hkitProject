from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, answer, question, result, save, session, stt
from app.store import init_csv

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 프론트 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_csv()


app.include_router(session.router, prefix="/session", tags=["Session"])
app.include_router(question.router, prefix="/question", tags=["Survey"])
app.include_router(answer.router, prefix="/answer", tags=["Answer"])
app.include_router(result.router, prefix="/result", tags=["Data"])
app.include_router(save.router, prefix="/save", tags=["Data"])
app.include_router(stt.router, prefix="/stt", tags=["Utility"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


# 루트 경로 생성
@app.get("/")
def root():
    return {"status": "ok", "message": "Server Working..."}
