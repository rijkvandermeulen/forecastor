from sqlalchemy import Column, Integer, String, Float, Date, text

from .database import Base, engine


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


def cleanup_database():
    """
    Clean up the database by deleting all records from specified tables.
    """
    print("Starting database cleanup...")
    TABLES_TO_CLEAN = [SalesAndForecastData.__tablename__, Parameters.__tablename__]
    with engine.connect() as connection:
        try:
            for table in TABLES_TO_CLEAN:
                connection.execute(text(f"DELETE FROM {table}"))
            connection.commit()
            print("Database cleanup completed successfully.")
        except Exception as e:
            print(f"An error occurred during cleanup: {e}")
