import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sqlalchemy import extract, func, and_
from sqlalchemy.orm import Session

from sqlalchemy.ext.asyncio import AsyncSession
from ViewModels import GetHistoryModel
from models import TransactionPart



class StatisticService:
    def __init__(self,db:Session):
        self._db = db


    

    def GetDayStatistic(self,model:datetime):
        start_date = datetime(model.year, model.month, model.day)
        end_date = datetime(model.year, model.month, model.day+1)
        data =  self.GetStatistic(start_date= start_date,end_date=end_date)

    def GetMouthStatistic(self,model:datetime):
        start_date = datetime(model.year, model.month, 1)
        end_date = datetime(model.year, model.month+1, 1)
        data =  self.GetStatistic(start_date= start_date,end_date=end_date)
        
    def GetYearStatistic(self, model:datetime):
        start_date = datetime(model.year, 1, 1)
        end_date = datetime(model.year+1, 1, 1)
        data =  self.GetStatistic(start_date,end_date)

    def GetStatistic(self, start_date:datetime,end_date:datetime):
        all_sales =  self._db.query(TransactionPart
        ).filter(and_(TransactionPart.date_buy >= start_date,
        TransactionPart.date_buy < end_date)).count()
        on_price =  self._db.query(func.sum(TransactionPart.price)
        ).filter(and_(TransactionPart.date_buy >= start_date,
        TransactionPart.date_buy < end_date)).scalar()
        commission =  self._db.query(func.sum(TransactionPart.commission)
        ).filter(and_(TransactionPart.date_buy >= start_date,
        TransactionPart.date_buy < end_date)).scalar()
        return {"sales": all_sales, "sum": on_price,"commission":commission}
    
    def ForecastNextYear(self):
        # 1. Сбор данных за 2 года по месяцам
        start_date = datetime(datetime.now().year - 2, 1, 1)
        end_date = datetime(datetime.now().year, 1, 1)

        monthly_data = self._db.query(
            extract('year', TransactionPart.date_buy).label('year'),
            extract('month', TransactionPart.date_buy).label('month'),
            func.count().label('sales'),
            func.sum(TransactionPart.price).label('revenue'),
            func.sum(TransactionPart.commission).label('commission')
        ).filter(
            TransactionPart.date_buy >= start_date,
            TransactionPart.date_buy < end_date
        ).group_by('year', 'month'
        ).order_by('year', 'month'
        ).all()

        # 2. Преобразование в DataFrame
        df = pd.DataFrame(monthly_data, columns=["year", "month", "sales", "revenue", "commission"])
        if df.empty:
            raise ValueError("Недостаточно данных для прогноза. Убедитесь, что в базе есть транзакции за последние 2 года.")
        df["time_index"] = range(len(df))

        forecast_result = {}

        for column in ["sales", "revenue", "commission"]:
            model = LinearRegression()
            model.fit(df[["time_index"]], df[column])
            future_index = np.arange(len(df), len(df) + 12).reshape(-1, 1)
            forecast = model.predict(future_index)
            forecast_result[column] = forecast

        # 3. Возврат прогноза по месяцам
        forecast_df = pd.DataFrame({
            "month": pd.date_range(start=f"{datetime.now().year}-01-01", periods=12, freq="MS").strftime("%Y-%m"),
            "predicted_sales": forecast_result["sales"].round().astype(int),
            "predicted_sum": forecast_result["revenue"].round(2),
            "predicted_commission": forecast_result["commission"].round(2),
        })

        return forecast_df.to_dict(orient="records")