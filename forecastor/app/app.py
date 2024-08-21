from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import models
from database.database import engine, get_db
from routers import upload

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(upload.router)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/results_summary", response_class=HTMLResponse)
async def get_high_level_summary_results(request: Request, db: Session = Depends(get_db)):

    data = db.query(models.SalesAndForecastData).all()

    return templates.TemplateResponse("results_summary.html", {"request": request, "data": data})
