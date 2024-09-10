from sqlalchemy import Column, Integer, String, Float, Date

from .database import Base


class SalesAndForecastData(Base):
    __tablename__ = "sales_and_forecast_data"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    sku = Column(String, index=True)
    date = Column(Date)
    sales = Column(Float)
    statistical_forecast = Column(Float)
    final_forecast = Column(Float)
    benchmark_forecast = Column(Float)
    absolute_error_stat_fcst = Column(Float)
    absolute_error_fin_fcst = Column(Float)
    absolute_error_bm_fcst = Column(Float)


class Parameters(Base):
    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    time_lag = Column(Integer)
