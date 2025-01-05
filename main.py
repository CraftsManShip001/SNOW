import requests
from datetime import datetime
import xmltodict
import tensorflow as tf
import numpy as np
import os
from dotenv import load_dotenv
load_dotenv()

KEY = os.getenv("KEY")

def get_current_date():
    current_date = datetime.now().date()
    return current_date.strftime("%Y%m%d")

def get_current_hour():
    now = datetime.now()
    return datetime.now().strftime("%H%M")

def forecast(params):
    try:
        url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
        res = requests.get(url, params)
        xml_data = res.text
        dict_data = xmltodict.parse(xml_data)

        print(dict_data)  # 응답 데이터 확인용 출력

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

@app.get('/snow')
def getSnowpercent():
    params ={'serviceKey' : KEY, 
         'pageNo' : '1', 
         'numOfRows' : '10', 
         'dataType' : 'XML', 
         'base_date' : get_current_date(), 
         'base_time' : get_current_hour(), 
         'nx' : '55', 
         'ny' : '127' }
    today_temp,today_rain = forecast(params)
    today_temp = float(today_temp)
    today_rain = float(today_rain)
    snow = tf.keras.models.load_model('./snowpredict/snowmodel.keras')
    result = snow.predict(np.array([[today_temp,today_rain]]))
    result = float(result[0][0])
    return {'temp':today_temp, 'rain':today_rain, 'snow':result}