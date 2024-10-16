from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pandas as pd

Base = declarative_base()                                                   # Создаем базовый класс для моделей

class WeatherData(Base):
    __tablename__ = 'weather_data'                                          # Создаём таблицу указываем столбцы и их названия
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now().replace(microsecond=0), name='Дата')
    temperature_2m = Column(String, nullable=False, name='Температура')
    precipitation = Column(Float, nullable=False, name='Осадки')
    surface_pressure = Column(String, nullable=False, name='Давление')
    wind_speed_10m = Column(String, nullable=False, name='Скорость ветра')
    wind_direction_10m = Column(String, nullable=False, name='Направление ветра')



engine = create_engine('sqlite:///../db/weather.db')                        # Указываем драйвер для работы с базой данных

Base.metadata.create_all(engine)                                            # Создаём таблицу

Session = sessionmaker(bind=engine)                                         # Создаём сессию для работой с бд
session = Session()


def export_last_10_to_excel():
    
    last_10_records = session.query(WeatherData).order_by(WeatherData.id.desc()).limit(10).all()        # Берём последние 10 записей в таблице
    
    data = [                                                                                            # Форматируем записи в удобный формат
        {
            'ID': record.id,
            'Дата': record.timestamp,
            'Температура': record.temperature_2m,
            'Осадки': record.precipitation,
            'Давление': record.surface_pressure,
            'Скорость ветра': record.wind_speed_10m,
            'Направление ветра': record.wind_direction_10m
        }
        for record in last_10_records
    ]
    
    data = data[::-1]                                                                                   # Инверсировал данные для красивого отображения в Exel

    df = pd.DataFrame(data)
    
    output_file = '../exel_db/weather_data.xlsx'                                                        # Сохраняем данные в Exel
    df.to_excel(output_file, index=False)

    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a') as writer:                            # Устанавливил ширину столбцам опять же для красоты и корректной читаемости
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        column_widths = {
            'A': 5,    # ID
            'B': 20,   # Дата
            'C': 15,   # Температура
            'D': 10,   # Осадки
            'E': 10,   # Давление
            'F': 15,   # Скорость ветра
            'G': 20    # Направление ветра
        }

        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width
    
    print(f"Последние 10 записей были успешно сохранены в {output_file}")
