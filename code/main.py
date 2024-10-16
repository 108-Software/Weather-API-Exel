import openmeteo_requests
import db
import time
from datetime import datetime
import threading
import requests_cache
from retry_requests import retry


def main():
    
    threading.Thread(target=command_listener, daemon=True).start()                      # Запуск фонового потока для обработки команды export

    while True:
        main_response()
        time.sleep(180)                                                                 # Ожидание 3 минуты перед следующим запросом


def main_response():
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)           # Настройка API-клиента 
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Параметры запроса
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 55.41,  # Долгота и широта сколтеха
        "longitude": 52.14,
        "current": [
            "temperature_2m",       # Температура 
            "precipitation",        # Тип осадков и их колличество
            "surface_pressure",     # Давление воздуха
            "wind_speed_10m",       # Скорость ветра
            "wind_direction_10m"    # Направление ветра
        ],
        "wind_speed_unit": "ms",
        "forecast_days": 1
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    current = response.Current()                                                        # Извлекаем текущие значения
    current_temperature_2m = current.Variables(0).Value()
    current_precipitation = current.Variables(1).Value()
    current_surface_pressure = current.Variables(2).Value()
    current_wind_speed_10m = current.Variables(3).Value()
    current_wind_direction_10m = current.Variables(4).Value()

    current_wind_direction = wind_direction(current_wind_direction_10m)

    
    weather_data = db.WeatherData(                                                      # Запись в базу данных
        timestamp=datetime.now().replace(microsecond=0),                                # Устанавливаем текущее время при добавлении записи
        temperature_2m="{:.2f} °C".format(current_temperature_2m),
        precipitation=current_precipitation,
        surface_pressure="{:.2f} мм. рт. ст.".format(current_surface_pressure),
        wind_speed_10m="{:.2f} м/с".format(current_wind_speed_10m),
        wind_direction_10m=current_wind_direction
    )
    db.session.add(weather_data)
    db.session.commit()

    print("Successfully API response" + "               Доступна команда export")



def wind_direction(current_wind_direction_10m):         # В случае с направлением ветра мы получаем ответ в градусах поэтому эта функция для определения направления
    if current_wind_direction_10m >= 337.5 or current_wind_direction_10m < 22.5:
        return "Север"
    elif 22.5 <= current_wind_direction_10m < 67.5:
        return "Северо-восток"
    elif 67.5 <= current_wind_direction_10m < 112.5:
        return "Восток"
    elif 112.5 <= current_wind_direction_10m < 157.5:
        return "Юго-восток"
    elif 157.5 <= current_wind_direction_10m < 202.5:
        return "Юг"
    elif 202.5 <= current_wind_direction_10m < 247.5:
        return "Юго-запад"
    elif 247.5 <= current_wind_direction_10m < 292.5:
        return "Запад"
    elif 292.5 <= current_wind_direction_10m < 337.5:
        return "Северо-запад"


def async_export_to_excel():                                                            # Функция для асинхронного экспорта данных в Excel
    threading.Thread(target=db.export_last_10_to_excel).start()


def command_listener():                                                                 # Функция слушатель ввода команды для экспорта данных из базы данных 
    while True:                                                                         # в эксель
        command = input()                               
        if command.strip().lower() == 'export':
            async_export_to_excel()
        else:
            print("Неизвестная команда. Попробуйте 'export' для экспорта данных в Excel.")


if __name__ == '__main__':
    main()                                                                              # Запуск основного процесса
    
