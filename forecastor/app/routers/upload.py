from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import io

from database.database import get_db
from database.models import SalesAndForecastData

router = APIRouter()


@router.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, detail="Invalid file format. Please upload a CSV file.")

    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

    print(df.head())
    for _, row in df.iterrows():
        print(row)
        db_record = SalesAndForecastData(
            demand_forecasting_unit=row['demand_forecasting_unit'],
            sales=row['sales'],
            statistical_forecast=row['statistical_forecast'],
            final_forecast=row['final_forecast']
        )
        db.add(db_record)
    db.commit()

    return {"filename": file.filename, "status": "Data processed successfully"}
