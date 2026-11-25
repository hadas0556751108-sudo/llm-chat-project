
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from run_agent import run_agent

app = FastAPI()


class PostRequest(BaseModel):
    post_subject: str
    new_post: str
    userId: int


@app.get("/")
def home():
    return FileResponse(
        Path(__file__).parent / "index.html"
    )


@app.post("/api/post")
def submit_post(request: PostRequest):

    result = run_agent(
        post_subject=request.post_subject,
        new_post=request.new_post,
        userId=request.userId
    )

    return result
