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

class update_data():
    def __init__(self):
        self.today=datetime.datetime.today()
        self.func_="每日股價爬蟲,更新_每日股價,月報表爬蟲,更新_月報表,營益分析彙總表爬蟲,更新_營益分析彙總表"
        db =sqlite3.connect(os.path.join('data.db'))
        
        s1='SELECT  max(date)  FROM daily_price_上市'
        df1=pd.read_sql(con=db,sql=s1)
        self.daily_price_last_day=datetime.datetime.strptime(df1["max(date)"].values[0], "%Y-%m-%d %H:%M:%S")
        
        s2='SELECT  max(date)  FROM daily_price_上櫃'
        df2=pd.read_sql(con=db,sql=s2)
        self.daily_price_上櫃_last_day=datetime.datetime.strptime(df2["max(date)"].values[0], "%Y-%m-%d %H:%M:%S")
        
        s3='SELECT  max(date)  FROM daily_price_三大法人'
        df3=pd.read_sql(con=db,sql=s3)
        self.daily_price_data_三大法人_last_day=datetime.datetime.strptime(df3["max(date)"].values[0], "%Y-%m-%d %H:%M:%S")
        
        self.function="每日股價爬蟲_上市,每日股價爬蟲_上櫃,更新_daily_price,月報表爬蟲,更新_月報表,營益分析彙總表爬蟲,更新_營益分析彙總表"
        print("每日股價最新日期(上市):",self.daily_price_last_day)
        print("每日股價最新日期(上櫃):",self.daily_price_上櫃_last_day)
        print("每日股價最新日期(三大法人):",self.daily_price_data_三大法人_last_day)
        #print("月營業收入表最新日期:",self.月營業收入表_last_day)
        #print("營益分析彙總表最新日期:",self.營益分析彙總表_last_day)
    #------------------------------------------------------------------------------------------
    def generate_year_seasonlist(self,start_year,end_year,season_list):
        yearslist=[]
        for year in range(start_year,end_year+1):
            for s in season_list: 
                yearslist.append((year,s))
        return yearslist
    #------------------------------------------------------------------------------------------
    def generate_monthlist(self,year,start_month,end_month):
        monthlist=[]
        for x in range(start_month,end_month+1):
            monthlist.append(datetime.datetime(year,x,1)) 
        return monthlist
    #------------------------------------------------------------------------------------------
    def generate_dayslist(self,start_date,end_date):
        if type(start_date) == datetime.datetime and type(end_date) == datetime.datetime:
            dayslist=[]
            while start_date<=end_date:
                dayslist.append(start_date)
                start_date+=datetime.timedelta(days=1)
            return dayslist
        else:
            print("Please enter an datetime obeject")
            return None
    #---------------------------------------------------------------------------------------------------
    def 每日股價爬蟲_上市(self,date):
        str_date = date.strftime('%Y%m%d')

        url='http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + str_date + '&type=ALLBUT0999'
        print(url)
        headers = {'user-agent': 'Mozilla/5.0'}
        r = requests.get(url,headers)
        #提取需要的資訊
        content = r.text.replace('=', '')
        lines = content.split('\n')
        lines = list(filter(lambda l:len(l.split('",')) > 10, lines))
        content = "\n".join(lines)
       
        #檢查該日期是否有爬出資料
        try:
            df = pd.read_csv(StringIO(content))
        except Exception as e:
            print('❌WARRN: cannot get stock price (上市) at', str_date)
            return None 
        #整理dataframe
        df_stockid=df["證券代號"]
        df_name=df["證券名稱"]
        df=df.astype("string")
        for columns in df.columns:
            df[columns]=df[columns].str.replace(",","")
        df = df.apply(lambda s:pd.to_numeric(s, errors='coerce'))
        df["證券名稱"]=df_name
        df["證券代號"]=df_stockid
        df = df[df.columns[df.isnull().all() == False]]
        df['date'] = pd.to_datetime(date.date())
        
        df=df.set_index(["date","證券代號"])
        return  df
    #---------------------------------------------------------------------------------------------------
    def 每日股價爬蟲_上櫃(self,date):
        
        str_date= str(date.year-1911)+date.strftime('/%m/%d')
        link = f'http://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_download.php?l=zh-tw&d={str_date}&s=0,asc,0'
        headers = {'user-agent': 'Mozilla/5.0'}
        r = requests.get(link,headers)
        print(link)
        lines = r.text.replace('\r', '').split('\n')
        try:
            df = pd.read_csv(StringIO("\n".join(lines[3:])), header=None)
            df.columns = list(map(lambda l: l.replace(' ',''), lines[2].split(',')))
        except:
            print('❌WARRN: cannot get stock price (上櫃) at', str_date)
            return None
        
        df=df.assign(date="")
        df.loc[:,'date']= pd.to_datetime(date.date())
        df_上櫃=df[df['代號'].str.len()==4]
        df_上櫃.rename(columns={'代號':'證券代號',
                       '名稱':'證券名稱','收盤':'收盤價','漲跌':'漲跌價差','開盤':'開盤價', 
                       '最高':'最高價', 
                       '最低':'最低價','成交金額(元)':'成交金額',
                       '最後買價':'最後揭示買價',
                       '最後買量(千股)':'最後揭示買量',  
                       '最後賣價':'最後揭示賣價',
                       '最後賣量(千股)':'最後揭示賣量'
                        } ,inplace=True)

        #df_上櫃['date']=pd.to_datetime(date.date())
        df_上櫃=df_上櫃[['date','證券代號','證券名稱','成交股數','成交筆數','成交金額','開盤價','最高價', '最低價', '收盤價','漲跌價差','最後揭示買價','最後揭示買量','最後揭示賣價','最後揭示賣量']]
        df_上櫃=df_上櫃.set_index(["date","證券代號"])
        df_上櫃=df_上櫃.replace(to_replace ="---",value =np.nan)
        for columns in df_上櫃.columns:
            df_上櫃[columns]=df_上櫃[columns].str.replace(",","")

        return  df_上櫃
    #------------------------------------------------------------------------------------------
    def 每日三大法人爬蟲(self,date):
        
        str_date = date.strftime('%Y%m%d')
        link = f'https://www.twse.com.tw/fund/T86?response=csv&date={str_date}&selectType=ALLBUT0999'
        headers = {'user-agent': 'Mozilla/5.0'}
        r = requests.get(link,headers)
        print(link)
        lines = r.text.replace('\r', '').split('\n')
        try:
            df = pd.read_csv(StringIO("\n".join(lines[3:])), header=None)
        except:
            print('❌WARRN: cannot get 三大法人(上市) at', str_date)
            return None 
        collist=lines[1].split(',')
        collist_new=[]
        for col in collist:
            collist_new.append(col.replace("\"",""))
        df.columns=list(map(lambda l: l.replace(' ',''), collist_new))
        df['證券代號']=df['證券代號'].str.replace("=","")
        df['證券代號']=df['證券代號'].str.replace("\"","")
        
        df=df.drop([''],axis=1)
        

        df=df.dropna(axis=0,how='all',subset=df.columns[2:18])
        df['date']=pd.to_datetime(date.date())
        df=df.set_index(["date","證券代號"])
        #------------------------------------------------------------------------------------------------------------
        str_date= str(date.year-1911)+date.strftime('/%m/%d')
        link2=f'https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&o=csv&se=AL&t=D&d={str_date}&s=0,asc'
        r=requests.get(link2)

        print(link2)

        lines = r.text.replace('\r', '').split('\n')
        try:
            df2 = pd.read_csv(StringIO("\n".join(lines[2:])), header=None)
        except:
            print('**WARRN: cannot get 三大法人(上櫃) at', str_date)
            return None 
        df2.columns=lines[1].split(",")

        dropcol=['外資及陸資-買進股數', '外資及陸資-賣出股數', '外資及陸資-買賣超股數','自營商-買進股數', '自營商-賣出股數','自營商-買賣超股數']

        df2=df2.drop(dropcol,axis=1)
        
        #更改col名稱
        df2.columns=['證券代號', '證券名稱', 
                    '外陸資買進股數(不含外資自營商)', '外陸資賣出股數(不含外資自營商)',
                    '外陸資買賣超股數(不含外資自營商)', 
                    '外資自營商買進股數', '外資自營商賣出股數', '外資自營商買賣超股數', 
                    '投信買進股數','投信賣出股數', '投信買賣超股數', 
                    '自營商買進股數(自行買賣)', '自營商賣出股數(自行買賣)','自營商買賣超股數(自行買賣)', 
                    '自營商買進股數(避險)', '自營商賣出股數(避險)', '自營商買賣超股數(避險)',
                    '三大法人買賣超股數']
        #排序column順序
        df2=df2[['證券代號', '證券名稱',
                '外陸資買進股數(不含外資自營商)', '外陸資賣出股數(不含外資自營商)',
                '外陸資買賣超股數(不含外資自營商)', 
                '外資自營商買進股數', '外資自營商賣出股數', '外資自營商買賣超股數', 
                '投信買進股數','投信賣出股數', '投信買賣超股數', 
                '自營商買進股數(自行買賣)', '自營商賣出股數(自行買賣)','自營商買賣超股數(自行買賣)',
                '自營商買進股數(避險)', '自營商賣出股數(避險)', '自營商買賣超股數(避險)',
                '三大法人買賣超股數']]

        df2['date']=pd.to_datetime(date.date())
        
        df2=df2[df2['證券代號'].str.len()==4]

        df2=df2.set_index(['date','證券代號'])        

        df_all=pd.concat([df,df2],axis=0)
        df_all.rename(columns={'外陸資買進股數(不含外資自營商)':'外陸資買進股數_不含外資自營商',
                               '外陸資賣出股數(不含外資自營商)':'外陸資賣出股數_不含外資自營商',
                               '外陸資買賣超股數(不含外資自營商)':'外陸資買賣超股數_不含外資自營商'} ,inplace=True)
        for col in df_all.columns:
            df_all[col]=df_all[col].astype("string")
        for columns in df_all.columns[1:20]:
            df_all[columns]=df_all[columns].str.replace(",","")
        
        #建立[自營商買賣超股數]column
        
        df_all['自營商買賣超股數']=df_all['自營商買賣超股數(自行買賣)'].astype("float")+df_all['自營商買賣超股數(避險)'].astype("float")
        for col in  df_all.columns:
            try:
                df_all[col]=df_all[col].astype('float')
            except:
                df_all[col]=df_all[col]
        return df_all
    #------------------------------------------------------------------------------------------
    def 更新_每日股價(self):
        if  (self.today.date()==self.daily_price_last_day.date() and self.today.date()==self.daily_price_上櫃_last_day.date() 
             and self.today.date()==self.daily_price_data_三大法人_last_day.date() ):
            print("data in today have been updated")
            return 
        
        start_date=min(self.daily_price_上櫃_last_day,self.daily_price_last_day,self.daily_price_data_三大法人_last_day
                       )+datetime.timedelta(days=1)
        end_date=self.today

        dayslist=self.generate_dayslist(start_date,end_date)
        
        db =sqlite3.connect(os.path.join('data.db'))
        
        for date in dayslist:
            #若為六日
            if date.weekday()>4:
                print("skip crawling data in ",date.strftime('%Y/%m/%d'),",it is weekend")
                continue
                
            else:
                data_上市=self.每日股價爬蟲_上市(date)
                data_上櫃=self.每日股價爬蟲_上櫃(date)
                data_三大法人=self.每日三大法人爬蟲(date)
            
                try :
                    if self.today.date()!=self.daily_price_last_day.date():
                        data_上市.to_sql("daily_price_上市",db,if_exists='append')
                        print("👍上市 data in", date.strftime('%Y/%m/%d'),"has been saved into data.db")
                        self.daily_price_last_day=date
                except:
                    print("❌上市data is empty,check whether it is holiday or data cannot assign to database")
                try :
                    if self.today.date()!=self.daily_price_上櫃_last_day.date():
                        data_上櫃.to_sql("daily_price_上櫃",db,if_exists='append')
                        print("👍上櫃 data in", date.strftime('%Y/%m/%d'),"has been saved into data.db")
                        self.daily_price_上櫃_last_day=date
                except:
                    print("❌上櫃data is empty,check whether it is holiday or data cannot assign to database")
                try :
                    if self.today.date()!=self.daily_price_data_三大法人_last_day.date():
                        data_三大法人.to_sql("daily_price_三大法人",db,if_exists='append')
                        print("👍三大法人 data in", date.strftime('%Y/%m/%d'),"has been saved into data.db")
                        self.daily_price_data_三大法人_last_day=date
                except:
                    print("❌三大法人 data is empty,check whether it is holiday or data cannot assign to database")

            #休息
            if len(dayslist)>1:
                time.sleep(10)
        
        db.close()    
        print("All Done!")
    #------------------------------------------------------------------------------------------
    def 月報表爬蟲(self,date):
        
        url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(date.year - 1911)+'_'+str(date.month)+'.html'
        print(url)
        
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        
        # 下載該年月的網站 轉換成 dataframe
        
        r = requests.get(url, headers=headers)
        r.encoding = 'big5'
        html_df = pd.read_html(StringIO(r.text))
        
        df_list=[]
        #合併各個報表
        for df in html_df :
            if df.shape[1]<=2 :
                pass
            elif df.columns.dtype != "object":
                pass
            else:
                df_list.append(df)
        
        res = pd.concat([df for df in df_list],ignore_index=True) 

        
        #更改欄位
        newcolumns=[]
        for col in res.columns:
            newcolumns.append(col[1])
        res.columns=newcolumns
        
        res = res[res['公司代號'] != '合計']
        
        res['date']=date
        
        res = res.set_index(['公司代號','date'])
        
        res = res[res.columns[res.isnull().all() == False]]
        
        res = res[~res['當月營收'].isnull()]
        
        
        return res
    #----------------------------------------------------------------------------------------------------------------------------
    def 更新_月報表(self):
        if  self.today.strftime("%Y%m")==self.月營業收入表_last_day.strftime("%Y%m"):
            print("data in this month have been updated")
            return 
        
        start_month=int(self.每日股價_last_day.strftime("%m"))
        year=int(self.每日股價_last_day.strftime("%Y"))
        end_month=int(self.today.strftime("%m"))
        
        month_list_year=self.generate_monthlist(year,start_month,end_month)
        
        db =sqlite3.connect(os.path.join('data.db'))
        
        for date in month_list_year:
            
            str_date = date.strftime('%Y%m%d')
            
            try:
            
                df=self.月報表爬蟲(date)
            
                df.to_sql('月營業收入表',db,if_exists='append')
                print(f"{date.year}年{date.month}月 之月報表已儲存至data.db 中")
            except:
                這個年月=self.today.strftime("%Y%m")
                print(f"df is empty,check whether there is {這個年月} data")
            #休息
            time.sleep(20)
        db.close()    
        print("All Done!")
    #----------------------------------------------------------------------------------------------------------------------------
    
    def 營益分析彙總表爬蟲(self,year,season):

        if year >= 1000:
            year -= 1911


        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb06'


        r = requests.post(url, {
            'encodeURIComponent':1,
            'step':1,
            'firstin':1,
            'off':1,
            'TYPEK':'sii',
            'year':str(year),
            'season':str(season),
        })

        r.encoding = 'utf8'
        
        try:
            dfs = pd.read_html(r.text, header=0)
        except:
            print("can not get data in",str(year),"year",str(season),"season")
            return None
        df=dfs[0]
            
        df_代號=df["公司代號"]
        
        df_公司名稱=df['公司名稱']
        
        df=df.apply(lambda s:pd.to_numeric(s, errors='coerce'))
        
        df['公司名稱']=df_公司名稱
        df["公司代號"]=df_代號
        
        df = df[df.columns[df.isnull().all() == False]]
        
        
        
        df['date']=datetime.datetime(year+1911,(season*3-2),1)
        
        return df
 

    #--------------------------------------------------------------
    def 更新_營益分析彙總表(self,start_year,end_year,season_list):
        #season_list    ex:[1,2,3,4]
        if type(season_list)!=list:
            print("please enter a list type of season!")
            return None
        year_seasonlist=self.generate_year_seasonlist(start_year,end_year,season_list)
        
        for i in year_seasonlist:
            df=self.營益分析彙總表爬蟲(i[0],i[1])
        
            db = sqlite3.connect('data.db')
        
            try:
                df.to_sql("營益分析彙總表",db,if_exists='append')
                print("data ",i[0],"年第",i[1],"季","have been saved to sqlite")
            except:
                print("something wrong")
            
                #休息
            time.sleep(20)
if __name__ == '__main__':
    update_data=update_data()
    update_data.更新_每日股價()