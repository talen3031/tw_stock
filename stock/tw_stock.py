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

class tw_stock():
    def __init__(self):
        self.connect= sqlite3.connect('data.db')
        #證券代號=pd.read_sql(con=self.connect,sql='select distinct 證券代號 from daily_price ')
        #self.stocklist=證券代號['證券代號'].tolist()
        self.func_="get_stock ,get,get_均線,get_technical_index"
       
        table=self.connect.execute('SELECT name FROM sqlite_master WHERE type = "table"')
        table_names = [t[0] for t in list(table)]
        table_dict={}
        for tname in table_names:
            table=[]
            c =self.connect.execute('PRAGMA table_info(' + tname + ');')
            for cname in [i[1] for i in list(c)]:
                table.append(cname)
            table_dict[tname]=table
        self.table_dict=table_dict
        
        self.cache_memory=False
        self.cache_memory_data=[]
        
 #---------------------------------------------------------------------------------------------------------------------------------------
    def get_stock(self,stockid,start_date,end_date=datetime.datetime.today()+datetime.timedelta(days=1),均線=False):
        end_date_str=end_date.strftime("%Y-%m-%d")
        start_date_str=start_date.strftime("%Y-%m-%d")
        #上市上櫃 股價 where 證券代號="{stockid}
        query=f'select * from (select date,證券代號,證券名稱,收盤價,開盤價,最高價,最低價,成交股數,漲跌價差 from daily_price_上市 where daily_price_上市.date between "{start_date_str}" and "{end_date_str}" union select date,證券代號,證券名稱,收盤價,開盤價,最高價,最低價,成交股數,漲跌價差 from daily_price_上櫃 where daily_price_上櫃.date between "{start_date_str}" and "{end_date_str}") where 證券代號="{stockid}" '
        
        df = pd.read_sql(con=self.connect,sql=query,parse_dates=['date'])
        df.rename(columns={'證券代號':'stock_id','證券名稱':'stock_name','收盤價':'close', '開盤價':'open', '最高價':'high', '最低價':'low', '成交股數':'volume','漲跌價差':'spread'} ,inplace=True)
        
        #三大法人  where 證券代號="{stockid}
        query3=f'select date ,外陸資買賣超股數_不含外資自營商,投信買賣超股數,自營商買賣超股數,三大法人買賣超股數 from daily_price_三大法人 where date between "{start_date_str}" and "{end_date_str}" and 證券代號="{stockid}" '
        df_三大法人= pd.read_sql(con=self.connect,sql=query3, parse_dates=['date'])                
        #left join 2張table
        df=df.merge(df_三大法人,on=["date"],how='left')
        
        if 均線:
       
            line_range_list=list(map(int,input('輸入所要的均線天數(ex:10 20 30 60 100)  :').split()))
            for x in line_range_list:       
                    #計算SMA
                df[f"SMA_{x}"]=abstract.SMA(df,x)
                    #計算WMA
                wd = np.arange(1, x+1)
                df[f'WMA_{x}']=df["close"].rolling(x).apply(lambda x :sum(x*wd)/ wd.sum(), raw=True)
                    #計算EMA
                df[f'EMA_{x}']=EMA(df['close'],x)
                BBANDS=abstract.BBANDS(df)
                MACD = abstract.MACD(df)
                STOCH = abstract.STOCH(df)
                df=pd.concat([df,BBANDS,MACD,STOCH],axis=1)
                df.rename(columns={'slowk':'K','slowd':'D'},inplace=True)
                RSI = abstract.RSI(df)
                df['RSI']=RSI
        return df
 
#---------------------------------------------------------------------------------------------------------------------------------------
    def get(self,information,start_date,end_date=datetime.datetime.today()+datetime.timedelta(days=1)):
        end_date_str=end_date.strftime("%Y-%m-%d")
        start_date_str=start_date.strftime("%Y-%m-%d")
        daily_pricelist=['close','open','high','low','volume','SMA','EMA','WMA','外陸資買賣超股數_不含外資自營商','自營商買賣超股數','投信買賣超股數','三大法人買賣超股數']
        
        if information in daily_pricelist:
            
            if not self.cache_memory:
                #到資料庫抓資料
                #上市上櫃每日股價
                query=f'select date,證券代號,證券名稱,收盤價,開盤價,最高價,最低價,成交股數,漲跌價差 from daily_price_上市 where daily_price_上市.date between "{start_date_str}" and "{end_date_str}" union select date,證券代號,證券名稱,收盤價,開盤價,最高價,最低價,成交股數,漲跌價差 from daily_price_上櫃 where daily_price_上櫃.date between "{start_date_str}" and "{end_date_str}"'
                df = pd.read_sql(con=self.connect,sql=query, parse_dates=['date'])                
                #三大法人
                query3=f'select date,證券代號,外陸資買賣超股數_不含外資自營商,投信買賣超股數,自營商買賣超股數,三大法人買賣超股數 from daily_price_三大法人 where date between "{start_date_str}" and "{end_date_str}" '
                df_3 = pd.read_sql(con=self.connect,sql=query3, parse_dates=['date'])                
                #left join 2張table
                df=df.merge(df_3,on=["date","證券代號"],how='left')
                
                df.rename(columns={'證券代號':'stock_id','證券名稱':'stock_name','收盤價':'close', '開盤價':'open', '最高價':'high', '最低價':'low', '成交股數':'volume'} ,inplace=True)
                
                df=df.replace(to_replace ="---",value =np.nan)
                
                nan_index=df.index[df[['open','high','low','close']].isnull().any(axis=1)]
                df=df.drop(nan_index)
                
                #暫存資料 不用再去資料庫抓資料
                self.cache_memory=True
                self.cache_memory_data=df
            
            #到 cache_memory_data 抓取dataframe
            df=self.cache_memory_data

            dfpivot=df.pivot(index='date', columns='stock_id')[information]


            return dfpivot.astype('float')#dfpivot.dropna(how="all",axis=1).astype('float')
        

            

        if information in self.table_dict['月營業收入表']:
            s=f'select *  from 月營業收入表 where date between "{start_date_str}" and "{end_date_str}"  order by date'
            df = pd.read_sql(con=self.connect  ,sql=s , parse_dates=['date'])

            return df.pivot(index='date', columns='公司代號')[information]

        if information in self.table_dict['資產負債彙總表']:
            s=f'select *  from 資產負債彙總表 where strftime("%Y-%m-%d", date) BETWEEN "{start_date_str}" AND "{end_date_str}" '
            df = pd.read_sql(con=self.connect  ,sql=s , parse_dates=['date'])
            return df.pivot(index='date', columns='公司代號')[information]
        
        if information in self.table_dict['營益分析彙總表']:
            s=f'select *  from 營益分析彙總表 where date between "{start_date_str}" and "{end_date_str}"  order by date'
            df = pd.read_sql(con=self.connect  ,sql=s , parse_dates=['date'])
            return df.pivot(index='date', columns='公司代號')[information]

#----------------------------------------------------------------------------------------------------------------------------------------
    def get_均線(self,均線類型,kind_of_均線,均線_天數):
        df=kind_of_均線.copy()

        if df.shape[0]<均線_天數:
            print(f"not enough days input,when it calulate {均線類型}-{均線_天數} MA")
        else:
            if 均線類型=='SMA':
                x=int(均線_天數)

                return df.rolling(window=x).mean().dropna(how='all')

            elif 均線類型=='EMA':

                x=int(均線_天數)
                for c in df.columns:
                    df[c]=EMA(df[c].values.astype('float'),x)
                return df.dropna(how='all')

            elif 均線類型=='WMA':
                x=int(均線_天數)
                for c in df.columns:
                    wd = np.arange(1, x+1)
                    df[c]=df[c].rolling(x).apply(lambda x :sum(x*wd)/ wd.sum(), raw=True)
                return df.dropna(how='all')

#----------------------------------------------------------------------------------------------------------------------------------------
    
    def get_technical_index(self,information,closedf,opendf,highdf,lowdf,volumedf):
        
        technical_list=["KD","RSI","MACD","BBANDS","WILLR","OBV","PLUS_DI","MINUS_DI","ADX"]
        df_1=pd.DataFrame()
        df_2=pd.DataFrame()
        df_3=pd.DataFrame()
        if information in technical_list:

            for col in closedf.columns:
                coldict = {'close': closedf[col].values.astype('float'),
                'open': opendf[col].values.astype('float'),
                'high': highdf[col].values.astype('float'),
                'low': lowdf[col].values.astype('float'),
                'volume': volumedf[col].values.astype('float')}
                if information=="KD":
                    array=abstract.STOCH(coldict)
                    df_1[col]=array[0]
                    df_2[col]=array[1]    
                if information=="RSI":
                    df_1[col]=abstract.RSI(coldict)
                if information=="MACD":
                    array=abstract.MACD(coldict)
                    df_1[col]=array[0]
                    df_2[col]=array[1]
                    df_3[col]=array[2] 
                if information=="BBANDS":
                    array=abstract.BBANDS(coldict)
                    df_1[col]=array[0]
                    df_2[col]=array[1]
                    df_3[col]=array[2]
                if information=="WILLR":
                    array=abstract.WILLR(coldict)
                    df_1[col]=array
                if information=="OBV":
                    array=abstract.OBV(coldict)
                    df_1[col]=array
                if information=="PLUS_DI":
                    array=abstract.PLUS_DI(coldict)
                    df_1[col]=array
                if information=="MINUS_DI":
                    array=abstract.MINUS_DI(coldict)
                    df_1[col]=array
                if information=="ADX":
                    array=abstract.ADX(coldict)
                    df_1[col]=array
            if len(df_2.columns) == 0:
                return df_1.set_index(closedf.index)
            else:
                if len(df_3.columns) == 0:
                    return df_1.set_index(closedf.index),df_2.set_index(closedf.index)
                else :
                    return df_1.set_index(closedf.index),df_2.set_index(closedf.index),df_3.set_index(closedf.index)
        else :
            print(f"Please enter {technical_list}")
            return 
if __name__ == '__main__':
    tw_stock=tw_stock()