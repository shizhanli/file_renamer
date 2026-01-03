# file_renamer

這是一個小型工具，用檔案最後修改時間 mtime 來重新命名檔案，支援 2 種模式，preview 與 apply，並輸出報表方便檢查與留存。

## 核心概念

1. preview 只產生改名規劃與報表，不會真的改檔名  
2. apply 會真的改檔名，改完也會輸出執行結果報表  
3. 預設忽略隱藏資料夾與隱藏檔案，也就是名稱以 . 開頭者不處理  
4. 每個資料夾各自重新計數，命名以 mtime 為主，同一秒內用序號避免重複  

## 命名規則

新檔名格式如下：

YYYYMMDD_HHMMSS_序號2位數 原副檔名

例子：

20260103_154501_01.jpg  
20260103_154501_02.jpg  

說明：

1. 時間來自檔案 mtime，採用本機時間  
2. 同一秒內若有多個檔案，序號會依排序遞增  
3. 副檔名會保留  

## 專案結構

1. src 放主程式 renamer.py  
2. reports 放輸出報表，資料夾會保留在 repo 中  
3. LICENSE 授權檔  
4. README.md 使用說明  

## 執行需求

1. Python 3.10 以上  
2. 僅使用標準函式庫，不需要額外安裝套件  

## 使用方式

### 1 下載

把專案下載到本機後，進入專案資料夾。

### 2 preview 預覽模式

1. 執行  
   python src/renamer.py  
2. 依提示輸入  
   1 要處理的資料夾路徑  
   2 模式輸入 preview  
3. 程式會輸出預覽報表到 reports 資料夾  

### 3 apply 執行模式

強烈建議先跑過 preview 並確認報表內容正確再執行。

1. 執行  
   python src/renamer.py  
2. 依提示輸入  
   1 要處理的資料夾路徑  
   2 模式輸入 apply  
   3 再輸入 y 或 yes 確認執行  
3. 程式會真的改名，改完輸出 apply 報表到 reports 資料夾  

## 報表說明

報表為 csv，欄位如下：

folder, old_name, new_name, mtime, status, note

status 常見值：

1. PLAN 表示預計會改名  
2. SKIP 表示跳過，原因在 note  
3. DONE 表示已完成改名，只會出現在 apply 報表  
4. ERROR 表示執行失敗，原因在 note  

報表檔名：

1. preview_YYYYMMDD_HHMMSS.csv  
2. apply_YYYYMMDD_HHMMSS.csv  

## 安全與注意事項

1. apply 會直接改檔名，建議先備份，或先對測試資料夾測  
2. 若檔案正在被其他程式使用，可能導致改名失敗並標記 ERROR  
3. 若目標檔名已存在，會跳過並標記 SKIP  
4. 報表是你最重要的審核依據，請先看 preview 報表再執行 apply  

## 常見問題

### 1 apply 是什麼
apply 是真的執行改名的模式，preview 只做規劃與報表，不會改檔名。

### 2 為什麼會 SKIP
常見原因是目標檔名已存在，或檔名本來就已符合規則，會在 note 顯示原因。

### 3 為什麼會 ERROR
常見原因是檔案不存在，檔案被佔用，或檔案系統拒絕改名，會在 note 顯示原因。

## 授權

本專案採用 MIT License，詳見 LICENSE。
