import requests
import pandas as pd
from io import StringIO
import datetime 
import sqlite3
import time
import os
import numpy as np
from talib import EMA
from talib import abstract
from matplotlib import pyplot as plt

def 選股模式一(close,open_,high,volume,均線,五日均量,三大法人買賣超,x=-1):
    # 今日量大於 五日均量*1.382
    condition1=volume.iloc[x]>五日均量.iloc[x]*1.382
    #sma連續三天往上走
    condition2=均線.iloc[x]>均線.iloc[(x-1)]
    condition3=均線.iloc[(x-1)]>均線.iloc[(x-2)]
    #今日收盤價 >=  ma
    condition4=close.iloc[x]>=均線.iloc[x]
    #昨日日收盤價 >=ma
    condition5=close.iloc[(x-1)]<=均線.iloc[(x-1)]
    #今日最高價>=昨日最高價
    condition6=high.iloc[x]>=high.iloc[(x-1)]
    #今日收盤價>=昨日開盤價
    condition7=close.iloc[x]>=open_.iloc[(x-1)]
    #漲幅>3.618%
    condition8=(close.iloc[x]-close.iloc[(x-1)])/close.iloc[(x-1)]>0.03618
    #五日均量大於 300
    condition9=五日均量.iloc[x]/1000>=300
    #三大法人買賣超 大於0
    condition10=三大法人買賣超.iloc[x]>0 
    #-----------------------------------------------------------
    columns=close.iloc[-1][condition1&condition2 & condition3 & condition4 & condition5 & condition6 & condition7 & condition8 &condition9&condition10].index
    date=volume.iloc[x].name
    stocks=columns.values
    string=f"{date}符合選股模式一的股票有{len(stocks)}檔股票,包括:{stocks}"
    print(string)
    st={}
    st['string']=string
    st["stocks"]=stocks
    st["date"]=date
    return st
"""
K線在144均線之上 做多
股市盤整時不做(當5MA<收盤價<20MA)(這個條件之後可以視情況做更改)
入場訊號:Kd  macd 同時或是前後出現黃金交叉 且macd需在零軸下方 ==> 做多
"""
def 雙重金死叉策略(close,dfk,dfd,快線,慢線,x=-1):
    condition1=dfk.iloc[x-1]<dfd.iloc[x-1]
    condition2=dfk.iloc[x]>dfd.iloc[x]
    condition3=快線.iloc[x-1]<慢線.iloc[x]
    condition4=快線.iloc[x]>慢線.iloc[x]
    condition5=快線.iloc[x]<0
    columns=close.iloc[x][condition1 & condition2 & condition3 &condition4 & condition5].index
    #-----------------------------------------------------------
    date=close.iloc[x].name
    stocks=columns.values
    string=f"{date}符合雙重金死叉策略的股票有{len(stocks)}檔股票,包括:{stocks}"
    print(string)
    st={}
    st['string']=string
    st["stocks"]=stocks
    st["date"]=date
    return st
"""
Created on 2021/2/1
 
    主觀交易（dmi策略）                             
           簡述: 



obv:
先任意設定一起始值OBV_0，如10000。接著累算以後每日的OBV值  
其中t為當日值，t-1為前一日值，Volume為當日的成交量值：
OBV_t = OBV_t-1 + Volume      IF Close_t > Close_t-1
OBV_t = OBV_t-1               IF Close_t = Close_t-1
OBV_t = OBV_t-1 - Volume      IF Close_t < Close_t-1
並設置 obv_ema 週期=144天

開倉: k線在 ema144 之上  adx線>20 plusDI 在 minusDI 之上   obv 在 obv_ema 之上 做多

#出場訊號: 趨勢變換  plusDI 在 minusDI 之下 adx線>20   
"""
def dmi策略(close,low,OBV,obv_ema,EMA_144,MINUS_DI,PLUS_DI,ADX,x=-1):
    # k線在 ema144 之上  
    condition1=low.iloc[x]>EMA_144.iloc[x]
    #  plusDI 在 minusDI 之上  
    condition2=PLUS_DI.iloc[x]>MINUS_DI.iloc[x]
    #adx線>20
    condition3=ADX.iloc[x]>20
    #obv 在 obv_ema 之上 做多
    condition4=OBV.iloc[x]>obv_ema.iloc[x]
    columns=close.iloc[x][condition1 & condition2 & condition3 &condition4].index
    
    date=close.iloc[x].name
    stocks=columns.values
    string=f"{date}符合dmi策略的股票有{len(stocks)}檔股票,包括:{stocks}"
    print(string)
    st={}
    st['string']=string
    st["stocks"]=stocks
    st["date"]=date
    return st
"""

bbi短均線=8日均線+13日均線+ 21日均線+ 34日均線/4
bbi長均線=55日均線+89日均線+ 144日均線+ 233日均線/4

k線在bbi長均線之上  多頭
k線在bbi長均線之下  空頭

k線往下穿過Bbi短線 做空   之後k線往上穿過Bbi短線 平倉
k線往上穿過Bbi短線 做多   之後k線往下穿過Bbi短線 平倉

策略:(做多型)
    條件 : k線在bbi長線之上  & k線上穿過bbi短均線   5日均量大於20日均量 且5日均量往上走 -----> 買進
    
    停損停利:
    k線往下穿過Bbi短線 平倉 

                  
"""
def bbi策略(close,bbi短均線,bbi長均線,high,low,五日均量,二十日均量,x=-1):
    #k線在bbi長線之上
    condition1=low.iloc[x]>bbi長均線.iloc[x]
    #昨日k線在bbi短均線之下
    condition2=high.iloc[x-1]<bbi短均線.iloc[x-1]
    #今日k線上穿過bbi短均線
    condition3=high.iloc[x]>bbi短均線.iloc[x]
    #5日均量大於20日均量
    condition4=五日均量.iloc[x]>二十日均量.iloc[x]
    #且5日均量往上走
    condition5=五日均量.iloc[x]>五日均量.iloc[x-1]
    #-----------------------------------------------------------
    columns=close.iloc[x][condition1 & condition2 & condition3 &condition4 & condition5].index
    date=close.iloc[x].name
    stocks=columns.values
    string=f"{date}符合bbi策略策略的股票有{len(stocks)}檔股票,包括:{stocks}"
    print(string)
    st={}
    st['string']=string
    st["stocks"]=stocks
    st["date"]=date
    return st
def 漲幅大於(close,x=-1,趴數=0.09):
    condition1=(close.iloc[x]-close.iloc[(x-1)])/close.iloc[(x-1)]>=趴數
    columns=close.iloc[-1][condition1].index
    date=volume.iloc[x].name
    stocks=columns.values
    string=f"{date} 漲幅>={趴數*100}% 的股票有{len(stocks)}檔股票,包括:{stocks}"
    print(string)
    st={}
    st['string']=string
    st["stocks"]=stocks
    st["date"]=date
    return st
def 投信連三買超股數(投信,volume,x=-1):
    #投信連三天買超股數大於100張 且 當日買超股數佔總成交量股數的10%以上
    condition1=投信.iloc[x]>=100000
    condition2=投信.iloc[x-1]>=100000
    condition3=投信.iloc[x-2]>=100000
    condition4=(投信.iloc[x]/volume.iloc[x])>=0.1
    columns=投信.iloc[-1][condition1 & condition2 & condition3 & condition4].index
    date=volume.iloc[x].name
    stocks=columns.values
    string=f"{date} 投信連三天買超的股票有{len(stocks)}檔股票,包括:{stocks}"
    print(string)
    st={}
    st['string']=string
    st["stocks"]=stocks
    st["date"]=date
    return st
def 外陸資連三買超股數(外陸資,volume,x=-1):
    #外資連三天買超股數大於100張 且 當日買超股數佔總成交量股數的10%以上
    condition1=外陸資.iloc[x]>=100000
    condition2=外陸資.iloc[x-1]>=100000
    condition3=外陸資.iloc[x-2]>=100000
    condition4=(外陸資.iloc[x]/volume.iloc[x])>=0.1
    columns=外陸資.iloc[-1][condition1 & condition2 & condition3 & condition4].index
    date=volume.iloc[x].name
    stocks=columns.values
    string=f"{date} 外陸資連三天買超的股票有{len(stocks)}檔股票,包括:{stocks}"
    print(string)
    st={}
    st['string']=string
    st["stocks"]=stocks
    st["date"]=date
    return st