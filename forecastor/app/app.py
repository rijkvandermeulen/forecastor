import io
import uuid

import pandas as pd
import numpy as np
import json
from fastapi import FastAPI, Request, Query, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from utils import get_forecast_kpis, check_delimiter, moving_average_benchmark, validate_input

from database import models
from database.database import engine, get_db
from database.models import SalesAndForecastData
from database.models import Parameters

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/uploadfile/")
async def process_input_data(
        request: Request,
        time_lag: int = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, detail="Invalid file format. Please upload a CSV file.")

    contents = await file.read()
    file_object = io.StringIO(contents.decode('utf-8'))

    try:
        delimiter = check_delimiter(file_object)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

    assert delimiter is not None

    df = pd.read_csv(file_object, delimiter=delimiter)

    validation_result = validate_input(df)
    # validation_result["is_valid"] = True

    if validation_result["is_valid"]:
        df["date"] = pd.to_datetime(df["date"])
        session_id = str(uuid.uuid4())

        # Generate benchmark forecast
        df = moving_average_benchmark(df, time_lag)

        df["session_id"] = session_id

        # Calculate the absolute errors
        df["absolute_error_stat_fcst"] = abs(df["sales"] - df["statistical_forecast"])
        df["absolute_error_fin_fcst"] = abs(df["sales"] - df["final_forecast"])
        df["absolute_error_bm_fcst"] = abs(df["sales"] - df["benchmark_forecast"])

        # Update the database
        records = df.to_dict(orient='records')
        db.bulk_insert_mappings(SalesAndForecastData, records)
        db.commit()
        db.add(Parameters(session_id=session_id, time_lag=time_lag))
        db.commit()
        return RedirectResponse(url=f"/results_summary?session_id={session_id}", status_code=303)
    else:
        return templates.TemplateResponse("validation_error.html", {
            "request": request,
            "error_message": validation_result["error_message"],
            "error_details": validation_result["error_details"]
        })


@app.get("/results_summary", response_class=HTMLResponse)
async def get_high_level_summary_results(
        request: Request,
        session_id: str = Query(...),
        db: Session = Depends(get_db)
):

    res = db.query(models.SalesAndForecastData).filter(models.SalesAndForecastData.session_id == session_id).all()
    df = pd.DataFrame([record.__dict__ for record in res])

    kpis = get_forecast_kpis(df)

    return templates.TemplateResponse("results_summary.html", {"request": request, "kpis": kpis, "session_id": session_id})


@app.get("/details_enrichment", response_class=HTMLResponse)
async def get_details_enrichment(
        request: Request,
        session_id: str = Query(...),
        db: Session = Depends(get_db)
):
    res = db.query(models.SalesAndForecastData).filter(models.SalesAndForecastData.session_id == session_id).all()

    # For initial rendering of the chart
    df = pd.DataFrame([record.__dict__ for record in res])

    df_grouped = df.groupby(["date"], as_index=False).agg(
        sales=("sales", "sum"),
        statistical_forecast=("statistical_forecast", "sum"),
        final_forecast=("final_forecast", "sum"),
        benchmark_forecast=("benchmark_forecast", "sum")
    ).reset_index(drop=True)

    chart_data = json.dumps(
        {
            "date": pd.to_datetime(df_grouped["date"]).dt.strftime("%Y-%m-%d").tolist(),
            "sales": df_grouped["sales"].tolist(),
            "statistical_forecast": df_grouped["statistical_forecast"].replace(np.nan, None).tolist(),
            "final_forecast": df_grouped["final_forecast"].replace(np.nan, None).tolist(),
            "benchmark_forecast": df_grouped["benchmark_forecast"].replace(np.nan, None).tolist(),
        }
    )

    kpis = get_forecast_kpis(df)

    dfu_list = df["sku"].unique().tolist()

    return templates.TemplateResponse(
        "details_enrichment.html", {
            "request": request,
            "session_id": session_id,
            "chart_data": chart_data,
            "dfu_list": dfu_list,
            "kpis": kpis
        }
    )


@app.get("/api/get_single_dfu")
async def get_single_dfu(
        session_id: str = Query(...),
        dfu: str = Query(...),
        db: Session = Depends(get_db)
):

    if not dfu:  # when the user selects "All DFUs" in the dropdown
        res = db.query(models.SalesAndForecastData).filter(
            models.SalesAndForecastData.session_id == session_id
        ).all()
    else:
        res = db.query(models.SalesAndForecastData).filter(
            models.SalesAndForecastData.session_id == session_id,
            models.SalesAndForecastData.sku == dfu
        ).all()

    df = pd.DataFrame([record.__dict__ for record in res])

    kpis = json.dumps(get_forecast_kpis(df))

    if not dfu:
        df = df.groupby(["date"], as_index=False).agg(
            sales=("sales", "sum"),
            statistical_forecast=("statistical_forecast", "sum"),
            final_forecast=("final_forecast", "sum"),
            benchmark_forecast=("benchmark_forecast", "sum")
        ).reset_index(drop=True)

    chart_data_new = json.dumps(
        {
            "date": pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d").tolist(),
            "sales": df["sales"].tolist(),
            "statistical_forecast": df["statistical_forecast"].replace(np.nan, None).tolist(),
            "final_forecast": df["final_forecast"].replace(np.nan, None).tolist(),
            "benchmark_forecast": df["benchmark_forecast"].replace(np.nan, None).tolist(),
        }
    )

    return {"chart_data_new": chart_data_new, "kpis": kpis}
