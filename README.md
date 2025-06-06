# 台股量化分析與自動化回測平台

## 專案簡介
本專案是一套**台股量化投資資料平台**，涵蓋資料自動爬取、資料庫管理、技術指標計算、多因子選股、策略回測與視覺化。適合量化投資、技術分析、機器學習選股及回測驗證等場景。

---

## 目錄結構與檔案說明

| 檔案/資料夾         | 主要功能/用途                         |
|--------------------|-------------------------------------|
| `update_data.py`   | 台股每日/每月/每季資料爬蟲，存入SQLite資料庫 `data_test.db`(data_test.db僅包含2020-1-1 到 2022-3-31的資料,僅供測試) |
| `tw_stock.py`      | 台股原始資料、法人、財報等 API 介面，可批次產生技術指標、均線等因子 |
| `strategy.py`      | 各式選股與技術分析策略 function 實作（可擴充）         |
| `plot.py`          | 個股技術指標/價量/均線等視覺化繪圖工具               |
| `__init__.py`      | 專案 package 初始化                          |

---


## Requirement

- Python >= 3.8
- pandas
- numpy
- matplotlib
- TA-Lib
- requests
- sqlite3

## 常見功能範例

### Dashboard (`dashboard.ipynb`)
- 提供互動式台股資料查詢與視覺化。
- 查詢個股歷史行情、技術指標、法人籌碼等。
- 支援 K 線、均線、MACD、RSI 等指標圖表。
- 可即時檢視策略選股結果。

## 測試資料下載

由於測試用資料庫較大，請從 [Google Drive 下載 datatest.zip](https://drive.google.com/file/d/1G9T3DoqDkuVpx2HwmN86D-9cLLGBhA-z/view?usp=drive_link)  
下載後解壓縮，將 `data_test.db` 放到專案根目錄即可。
