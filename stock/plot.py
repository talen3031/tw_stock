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
import matplotlib
class plot():
    def __init__(self):
        self.connect= sqlite3.connect('data.db')
        self.func_="Technical_index_plot,price_and_volume_plot,MA_plot"
    def Technical_index_plot(self,stockid,start_date,end_date=datetime.datetime.today()+datetime.timedelta(days=1)):
        
        start_date_str=start_date.strftime("%Y-%m-%d")
        end_date_str=end_date.strftime("%Y-%m-%d")
        
        start_date_minus_365_str=(start_date-datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        
        s=f'select 證券代號,證券名稱, date, 開盤價, 收盤價, 最高價, 最低價, 成交股數,漲跌價差 from daily_price_上市 where 證券代號="{stockid}" and date between "{start_date_minus_365_str}" and "{end_date_str}"  UNION select 證券代號,證券名稱, date, 開盤價, 收盤價, 最高價, 最低價, 成交股數,漲跌價差 from daily_price_上櫃 where 證券代號="{stockid}" and date between "{start_date_minus_365_str}" and "{end_date_str}" order by date '

        df_all= pd.read_sql(con=self.connect,sql=s,index_col=['date'], parse_dates=['date'])
        df_all=df_all.dropna()
        df_all.rename(columns={'證券代號':'stock_id','證券名稱':'stock_name','收盤價':'close', '開盤價':'open', '最高價':'high', '最低價':'low', '成交股數':'volume','漲跌價差':'spread'} ,inplace=True)
        
        # 創建技術指標
        BBANDS=abstract.BBANDS(df_all)
        MACD = abstract.MACD(df_all)
        RSI = abstract.RSI(df_all)
        STOCH = abstract.STOCH(df_all)
        #選取我們要的日期
        df=df_all[start_date_str:end_date_str]
        BBANDS=BBANDS[start_date_str:end_date_str]
        MACD=MACD[start_date_str:end_date_str]
        RSI=RSI[start_date_str:end_date_str]
        STOCH=STOCH[start_date_str:end_date_str]
        
        #繪製圖表----------------------------------------------
        f, axs = plt.subplots(4,1,figsize=(25,15))
        ax1=axs[0]
        ax2=axs[1]
        ax3=axs[2]
        ax4=axs[3]
        #BBND AND STOCK_PRICE
        #ax1.plot(df['close'],label="Stock Price",color="red")
        for col in BBANDS.columns:
            ax1.plot(BBANDS[col],label=col)
        ax1.legend()
        ax1.set_title("BBND")
        ax1.grid(linestyle='dotted', linewidth=1)
        #RSI
        ax2.plot(RSI,color="purple")
        ax2.set_title("RSI")
        ax2.grid(linestyle='dotted', linewidth=1)
        #KD
        for col in STOCH.columns:
            ax3.plot(STOCH[col],label=col)
        ax3.legend()
        ax3.set_title("KD")
        ax3.grid(linestyle='dotted', linewidth=1)
        #MACD
        def color(df):
            bar_colorlist=[]
            for i,row in df.iterrows():
                    if row["macdhist"]>0:
                        bar_colorlist.append("r")
                    else:
                        bar_colorlist.append("g")
            return bar_colorlist
        
        ax4.bar(MACD["macdhist"].index,MACD["macdhist"],color=color(MACD))
        ax4.plot(MACD['macdsignal'],label="macdsignal")
        ax4.plot(MACD['macd'],label="macd")
        ax4.legend()
        ax4.legend()
        ax4.set_title("MACD")
        ax4.grid(linestyle='dotted', linewidth=1)

        plt.show()
    #---------------------------------------------------------------------------------------------------------------------------------------
    def price_and_volume_plot(self,stockid,start_date,end_date=datetime.datetime.today()+datetime.timedelta(days=1),SMA_days=[10,20,60]):
        
        start_date_str=start_date.strftime("%Y-%m-%d")
        end_date_str=end_date.strftime("%Y-%m-%d")
        
        start_date_minus_365_str=(start_date-datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        
        
        s=f'select 證券代號,證券名稱, date, 開盤價, 收盤價, 最高價, 最低價, 成交股數,漲跌價差 from daily_price_上市 where 證券代號="{stockid}" and date between "{start_date_minus_365_str}" and "{end_date_str}"  UNION select 證券代號,證券名稱, date, 開盤價, 收盤價, 最高價, 最低價, 成交股數,漲跌價差 from daily_price_上櫃 where 證券代號="{stockid}" and date between "{start_date_minus_365_str}" and "{end_date_str}" order by date '
        
        df_all= pd.read_sql(con=self.connect,sql=s,index_col=['date'], parse_dates=['date'])
        df_all=df_all.dropna()
        df_all.rename(columns={'證券代號':'stock_id','證券名稱':'stock_name','收盤價':'close', '開盤價':'open', '最高價':'high', '最低價':'low', '成交股數':'volume','漲跌價差':'spread'} ,inplace=True)
        
        
        
        df=df_all[start_date_str:end_date_str]
        stock_name=str(df['stock_name'][0])
        print(stock_name)
        #準備 color list
        def color(df):
            volume_colorlist=[]
            for i,row in df.iterrows():
                    if row["open"]>row["close"]:
                        volume_colorlist.append("g")
                    else:
                        volume_colorlist.append("r")
            return volume_colorlist
        f, axs = plt.subplots(1,2,figsize=(18,10))
        ax1=axs[0]
        ax2=axs[1]

        #準備 畫ax1 要用到的資料
        oc_min = pd.concat([df['open'], df['close']], axis=1).min(axis=1)
        oc_max = pd.concat([df['open'], df['close']], axis=1).max(axis=1)

        x= np.arange(len(df))        
        # 準備xticks label 
        if len(df.index)<=365:
            xindex=df.index.strftime("%m-%d")
        
        xindexlist=[]
        for x in xindex:
             xindexlist.append(x)
        for i,x in enumerate(xindexlist) :
            if i%4!=0:
                xindexlist[i]=""
            else:
                xindexlist[i]=x
       #Stock Price
        ax1.bar(xindex, oc_max-oc_min, bottom=oc_min, color=color(df), linewidth=0)
        ax1.vlines(xindex , df['low'], df['high'], color=color(df), linewidth=1)
        
        for day in SMA_days:
            SMA=df_all['close'].rolling(day).mean()
            SMA=SMA[start_date_str:end_date_str]
            ax1.plot(xindex,SMA,label=f"SMA_{day}")
        #ax1.plot(xindex,df['close'],label="price",color="red")
        ax1.legend()
        ax1.set_title(f"{stockid}stock price")
        ax1.set_xticklabels(xindexlist,fontsize=10,rotation=45)
        ax1.grid(linestyle='dotted', linewidth=1)
        #Volume 
        volume=df['volume']
        if volume.max() > 1000000:
            volume_scale = 'M'
            scaled_volume = volume / 1000000
        elif volume.max() > 1000:
            volume_scale = 'K'
            scaled_volume = volume / 1000

        ax2.bar(xindex, scaled_volume,color = color(df))
        ax2title=f'{stockid} Volume ,scale='+volume_scale
        ax2.set_title(ax2title)
        ax2.set_xticklabels(xindexlist,rotation=45)

        ax2.grid(linestyle='dotted', linewidth=1)
        plt.show()
        

        #------------------------------------------------------------------
    def MA_plot(self,stockid,start_date,end_date=datetime.datetime.today()+datetime.timedelta(days=1),均線="SMA"):
        
        line_range_list=list(map(int,input('輸入所要的均線天數(ex:10 20 30 60 100)  :').split()))
        
        start_date_str=start_date.strftime("%Y-%m-%d")
        end_date_str=end_date.strftime("%Y-%m-%d")
        
        start_date_minus_365_str=(start_date-datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        
        
        s=f'select 證券代號,證券名稱, date, 開盤價, 收盤價, 最高價, 最低價, 成交股數,漲跌價差 from daily_price_上市 where 證券代號="{stockid}" and date between "{start_date_minus_365_str}" and "{end_date_str}"  UNION select 證券代號,證券名稱, date, 開盤價, 收盤價, 最高價, 最低價, 成交股數,漲跌價差 from daily_price_上櫃 where 證券代號="{stockid}" and date between "{start_date_minus_365_str}" and "{end_date_str}" order by date '
        
        df_all= pd.read_sql(con=self.connect,sql=s,index_col=['date'], parse_dates=['date'])
        df_all=df_all.dropna()
        df_all.rename(columns={'證券代號':'stock_id','證券名稱':'stock_name','收盤價':'close', '開盤價':'open', '最高價':'high', '最低價':'low', '成交股數':'volume','漲跌價差':'spread'} ,inplace=True)
        
        for x in line_range_list:
            if type(x)!=int:
                print("please enter integer in list")
                return None
        
        for x in line_range_list:       
        #計算SMA
            df_all[f"SMA_{x}"]=abstract.SMA(df_all,x)
        #計算WMA
            wd = np.arange(1, x+1)
            df_all[f'WMA_{x}']=df_all["close"].rolling(x).apply(lambda x :sum(x*wd)/ wd.sum(), raw=True)
        #計算EMA
            df_all[f'EMA_{x}']=EMA(df_all['close'],x)
        df=df_all[start_date_str:end_date_str]
        
        
        if 均線=="SMA":
        #作圖
            f, ax = plt.subplots(1,1,figsize=(8,8))
            ax.plot(df["close"],label='close price',color="red")  
            for x in line_range_list:
                ax.plot(df[f"SMA_{x}"],label=f"SMA_{x}")
            ax.legend()
            ax.set_title(f"{stockid}SMA")
        elif 均線=="WMA":
        #作圖
            f, ax = plt.subplots(1,1,figsize=(8,8))
            ax.plot(df["close"],label='close price',color="red")  
            for x in line_range_list:
                ax.plot(df[f"SMA_{x}"],label=f"SMA_{x}")
            ax.legend()
            ax.set_title(f"{stockid}WMA")
        elif 均線=="EMA":
        #作圖
            f, ax = plt.subplots(1,1,figsize=(8,8))
            ax.plot(df["close"],label='close price',color="red")  
            for x in line_range_list:
                ax.plot(df[f"EMA_{x}"],label=f"EMA_{x}")
            ax.legend()
            ax.set_title(f"{stockid}EMA")
        elif  均線=="ALL":
            f, axs = plt.subplots(1,3,figsize=(14,8))
            ax1=axs[0]
            ax2=axs[1]
            ax3=axs[2]
            for x in line_range_list:
                ax1.plot(df["close"],label='close price',color="red")
                ax2.plot(df["close"],label='close price',color="red")
                ax3.plot(df["close"],label='close price',color="red")
                ax1.plot(df[f"SMA_{x}"],label=f"SMA_{x}")
                ax2.plot(df[f"WMA_{x}"],label=f"WMA_{x}")
                ax3.plot(df[f"EMA_{x}"],label=f"EMA_{x}")
    
            ax1.legend()
            ax2.legend()
            ax3.legend()
            ax1.set_title(f"{stockid}SMA")
            ax2.set_title(f"{stockid}WMA")
            ax3.set_title(f"{stockid}EMA")
        else:
            print('Error:Please enter \"SMA\",\"WMA\",\"EMA\"or\"ALL\" in last params')
            return None
        plt.show() 