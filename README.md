# file_renamer

file_renamer 是一個檔名整理工具，依檔案最後修改時間 mtime 重新命名檔案，支援 preview 與 apply 2 種模式，並輸出 CSV 報表，適合先檢查再執行。

## 1 這個工具解決什麼問題

當資料夾裡的檔名混亂，想要依時間排序並統一命名時，可用此工具將檔案改成可讀且可排序的格式，方便整理、歸檔、查找。

## 2 核心概念

1 preview 只產生改名計畫與報表，不會改動任何檔案  
2 apply 會先產生預覽報表，確認後才實際改名，並輸出執行結果報表  
3 工具會遞迴掃描子資料夾，並忽略隱藏資料夾與隱藏檔案，也就是名稱以 . 開頭者不處理  
4 命名以資料夾為單位各自編號，每個資料夾的序號都會從 01 開始  

## 3 命名規則

新檔名格式如下

YYYYMMDD_HHMMSS_序號2位數 原副檔名

例子

20260103_154501_01.jpg  
20260103_154501_02.jpg  
20260103_160010_01.pdf  

規則說明

1 YYYYMMDD_HHMMSS 取自檔案 mtime 的本機時間  
2 同一資料夾內若同一秒有多個檔案，序號依排序遞增 01 02 03  
3 副檔名沿用原檔案副檔名  

排序方式

1 以 mtime 由舊到新排序  
2 若 mtime 相同，則以原檔名文字順序排序  
3 排序僅用於產生序號的先後順序  

## 4 專案結構

1 src/renamer.py 主程式  
2 reports 報表輸出位置，資料夾會保留在 repo 中  
3 README.md 使用說明  
4 LICENSE 授權檔  

建議在 reports 放一個空檔案 .gitkeep，避免資料夾因為空而無法被 Git 追蹤。

## 5 執行需求

1 Python 3.10 以上  
2 僅使用標準函式庫，不需安裝第三方套件  

## 6 快速開始

在專案根目錄執行

python src/renamer.py

程式會詢問 2 個輸入

1 請輸入要處理的資料夾路徑  
2 請輸入模式 preview 或 apply  

建議流程

1 先跑 preview  
2 打開 reports 內的 preview 報表檢查是否符合預期  
3 確認無誤再跑 apply  

## 7 preview 模式

用途

1 只做規劃，不改動檔案  
2 產生 preview 報表，列出每個檔案的原名與預計新名  

輸出

1 會在 reports 產生 preview_YYYYMMDD_HHMMSS.csv  
2 終端機會顯示統計資訊，例如總檔案數，可改名數，跳過數，錯誤數  

## 8 apply 模式

用途

1 先產生改名計畫與 preview 報表  
2 需要二次確認，輸入 y 或 yes 才會開始改名  
3 實際改名後，輸出 apply 報表記錄結果  

輸出

1 會在 reports 產生 apply_YYYYMMDD_HHMMSS.csv  
2 終端機會顯示套用結果統計，例如已完成數，跳過數，錯誤數  

安全說明

1 apply 會直接改檔名，建議先備份，或先在複製出的測試資料夾驗證  
2 若檔案被其他程式占用，或權限不足，可能會出現 ERROR  
3 若目標檔名已存在，會跳過並標記 SKIP，原因會寫在 note  
4 apply 會採用兩階段改名，先改成暫存檔名，再改成最終檔名，以降低同名衝突風險  

## 9 報表說明

報表格式為 CSV，欄位如下

1 folder 檔案所在資料夾  
2 old_name 原檔名  
3 new_name 新檔名  
4 mtime 檔案修改時間，ISO 8601 格式  
5 status 狀態  
6 note 補充說明  

status 可能值

1 PLAN 表示預計改名，目標檔名不存在  
2 SKIP 表示跳過，原因在 note  
3 DONE 表示已成功改名，只會出現在 apply 後  
4 ERROR 表示改名失敗，原因在 note  

note 常見內容

1 already named 表示檔名已符合規則，不需改名  
2 target exists 表示目標檔名已存在  
3 duplicate target in plan 表示同一資料夾內計畫產生重複目標檔名  
4 source missing 表示來源檔案找不到  
5 temp rename failed 表示暫存改名失敗  
6 final rename failed 表示最終改名失敗  
7 rollback done 表示最終改名失敗後已嘗試回復原檔名  
8 rollback failed 表示回復原檔名也失敗  

## 10 範例

preview 範例輸入

1 請輸入要處理的資料夾路徑: C:\test_folder  
2 請輸入模式 preview 或 apply: preview  

apply 範例輸入

1 請輸入要處理的資料夾路徑: C:\test_folder  
2 請輸入模式 preview 或 apply: apply  
3 即將執行改名，是否繼續 (y 或 yes 才會執行): y  

## 11 已知限制

1 此工具以檔案 mtime 為依據，不讀取照片 EXIF 拍攝時間  
2 隱藏檔與隱藏資料夾不處理  
3 大量檔案時可能需要較長時間，建議先用小資料夾測試  

## 12 授權

本專案採用 MIT License
