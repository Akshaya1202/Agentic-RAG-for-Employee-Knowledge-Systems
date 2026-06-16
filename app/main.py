from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agents.hybrid_agents import run_query

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class QueryRequest(BaseModel):
    query: str


@app.get("/")
def index():
    return FileResponse(static_dir / "index.html")


@app.post("/ask")
def ask(payload: QueryRequest):
    result = run_query(payload.query)
    return result
