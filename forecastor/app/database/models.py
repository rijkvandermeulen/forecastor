from sqlalchemy import Column, Integer, String, Float, Date

from .database import Base


class SalesAndForecastData(Base):
    __tablename__ = "sales_and_forecast_data"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    demand_forecasting_unit = Column(String, index=True)
    date = Column(Date)
    sales = Column(Float)
    statistical_forecast = Column(Float)
    final_forecast = Column(Float)
