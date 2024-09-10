import uuid

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import pandas as pd
import io

from database.database import get_db
from database.models import SalesAndForecastData

from routers.utils import check_delimiter, moving_average_benchmark

from database.models import Parameters


router = APIRouter()


@router.post("/uploadfile/")
async def process_input_data(time_lag: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
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
