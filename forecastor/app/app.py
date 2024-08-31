import pandas as pd
from fastapi import FastAPI, Request, Depends, Query
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
async def get_high_level_summary_results(
        request: Request,
        session_id: str = Query(...),
        db: Session = Depends(get_db)
):

    res = db.query(models.SalesAndForecastData).filter(models.SalesAndForecastData.session_id == session_id).all()
    df = pd.DataFrame([record.__dict__ for record in res])

    # Calculate forecast accuracy of the various forecast versions
    mae_perc_stat_fcst = min(1, (df["absolute_error_stat_fcst"].sum() / df["sales"].sum()))
    fa_stat_fcst = (1 - mae_perc_stat_fcst) * 100
    mae_perc_fin_fcst = min(1, (df["absolute_error_fin_fcst"].sum() / df["sales"].sum()))
    fa_fin_fcst = (1 - mae_perc_fin_fcst) * 100
    mae_perc_bm_fcst = min(1, (df["absolute_error_bm_fcst"].sum() / df["sales"].sum()))
    fa_bm_fcst = (1 - mae_perc_bm_fcst) * 100

    # Deltas
    fva_fin_stat = fa_fin_fcst - fa_stat_fcst
    fva_bm_stat = fa_stat_fcst - fa_bm_fcst

    kpis = {
        "fa_stat_fcst": fa_stat_fcst,
        "fa_fin_fcst": fa_fin_fcst,
        "fa_bm_fcst": fa_bm_fcst,
        "fva_fin_stat": fva_fin_stat,
        "fva_bm_stat": fva_bm_stat
    }

    return templates.TemplateResponse("results_summary.html", {"request": request, "kpis": kpis, "session_id": session_id})


@app.get("/details_enrichment", response_class=HTMLResponse)
async def get_details_enrichment(
        request: Request,
        session_id: str = Query(...),
        db: Session = Depends(get_db)
):
    res = db.query(models.SalesAndForecastData).filter(models.SalesAndForecastData.session_id == session_id).all()
    df = pd.DataFrame([record.__dict__ for record in res])

    return templates.TemplateResponse("details_enrichment.html", {"request": request, "session_id": session_id})
