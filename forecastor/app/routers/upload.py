import uuid

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
import pandas as pd
import io

from database.database import get_db
from database.models import SalesAndForecastData

from routers.utils import check_delimiter

from database.models import Parameters

router = APIRouter()


@router.post("/uploadfile/")
async def submit_input_data(time_lag: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
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
    df["date"] = pd.to_datetime(df["date"], format='%Y-%m-%d')

    # Update the database
    records = df.to_dict(orient='records')
    session_id = str(uuid.uuid4())
    for record in records:
        record['session_id'] = session_id
    db.bulk_insert_mappings(SalesAndForecastData, records)
    db.commit()

    db.add(Parameters(session_id=session_id, time_lag=time_lag))
    db.commit()

    return {"filename": file.filename, "status": "Data processed successfully"}
