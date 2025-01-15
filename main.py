import requests
from datetime import datetime
from datetime import timedelta
from pydantic import BaseModel,Field
import pytz
import xmltodict
import tensorflow as tf
import numpy as np
import os
from dotenv import load_dotenv
load_dotenv()

KEY = os.getenv("KEY")

city_nx = {'Busan': 55, 'Seoul': 60, 'Daegu': 89, 'Incheon': 54, 'Daejeon': 67, 'Gwangju': 58, 'Ulsan': 102}
city_ny = {'Busan': 127, 'Seoul': 127, 'Daegu': 90, 'Incheon': 124, 'Daejeon': 100, 'Gwangju': 74, 'Ulsan': 84}

models = {
    'Busan': 'snowbusanmodel',
    'Seoul': 'snowseoulmodel',
    'Daegu': 'snowdaegumodel',
    'Incheon': 'snowincheonmodel',
    'Daejeon': 'snowdaejeonmodel',
    'Gwangju': 'snowgwangjumodel',
    'Ulsan': 'snowulsanmodel'
}


class City(BaseModel):
    city : str

def get_current_date():
    tz = pytz.timezone('Asia/Seoul')
    current_date = datetime.now(tz).date()
    return current_date.strftime("%Y%m%d")

def get_current_hour():
    tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(tz)
    if now.minute < 30:
        base_time = (now - timedelta(hours=1)).strftime("%H") + "30"
    else:
        base_time = now.strftime("%H") + "30"
    return base_time

def forecast(params):
    try:
        url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
        res = requests.get(url, params)
        xml_data = res.text
        dict_data = xmltodict.parse(xml_data)
        temp, sky = None, None
        for item in dict_data['response']['body']['items']['item']:
            if item['category'] == 'T1H':
                temp = item['obsrValue']
            if item['category'] == 'RN1':
                sky = item['obsrValue']
        return float(temp), float(sky)
    except Exception as e:
        print(f"Error fetching forecast data: {e}")
        return 0.0, 0.0

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "https://snow-front-7fpcqu3mn-craftsmanships-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 요청할 도메인
    allow_credentials=True,
    allow_methods=["*"],  # 모든 메서드 허용
    allow_headers=["*"],
)

@app.post('/snow')
def getSnowPercent(request : City):
    city = request.city
    nx = str(city_nx[city])
    ny = str(city_ny[city])
    params ={'serviceKey' : KEY, 
         'pageNo' : '1', 
         'numOfRows' : '10', 
         'dataType' : 'XML', 
         'base_date' : get_current_date(), 
         'base_time' : get_current_hour(), 
         'nx' : nx, 
         'ny' : ny }
    today_temp,today_rain = forecast(params)
    today_temp = float(today_temp)
    today_rain = float(today_rain)
    snow = tf.keras.models.load_model('./' + models[city] + '.keras')
    result = snow.predict(np.array([[today_temp,today_rain]]))
    result = float(result[0][0])
    if result <= 0.0001:
        result = float(0)
    return {'temp':today_temp, 'rain':today_rain, 'snow':result}