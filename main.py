import requests
from datetime import datetime
import xmltodict
import tensorflow as tf
import numpy as np
import os
from dotenv import load_dotenv
load_dotenv()

KEY = os.getenv("KEY")

print(KEY)

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

snow = tf.keras.models.load_model('./snowmodel.keras')
result = snow.predict(np.array([[today_temp,today_rain]]))
result = float(result[0][0])

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처 목록
    allow_credentials=True,
    allow_methods=["GET"],  # 허용할 HTTP 메서드
    allow_headers=["*"],  # 허용할 헤더
)

@app.get('/snow')
def getSnowpercent():
    return {'temp':today_temp, 'rain':today_rain, 'snow':result}

print('오늘의 날씨는 %.1f도이고 강수량은 %.1fmm 마지막으로 눈이 올 확률은 대충 %.3f%%입니다' %(today_temp,today_rain,result))