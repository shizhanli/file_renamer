# file_renamer

依檔案修改時間（mtime）遞迴重新命名檔案，提供 preview 與 apply 2 種模式，並輸出報表。若發生檔名衝突則跳過並記錄。

## 功能特色
1. 遞迴掃描指定資料夾內所有檔案（包含子資料夾）
2. 依檔案修改時間（mtime）產生新檔名
3. 命名格式：YYYYMMDD_HHMMSS_序號，例如 20260103_153012_01.jpg
4. 同一資料夾內若同一秒有多個檔案，自動以 01、02、03 編序
5. preview 模式只輸出報表，不改名
6. apply 模式執行改名
7. 若新檔名已存在則跳過，並在報表註記原因

## 使用方式
1. 下載或複製此 repo 到本機
2. 執行程式
   python src/renamer.py
3. 依提示輸入
   1 要處理的資料夾路徑
   2 模式 preview 或 apply

## 輸出報表
1. 報表會輸出到 reports 資料夾
2. 檔名格式：preview_YYYYMMDD_HHMMSS.csv
3. 欄位包含 folder、old_name、new_name、mtime、status、note

## 專案結構
1. src/renamer.py 主要程式
2. reports/ 報表輸出位置

## 目前狀態
1. preview 已完成：可掃描、產生改名計畫、輸出報表
2. apply 狀態：目前尚未真正執行改名流程（下一步將補齊）

## Roadmap
1. 完成 apply 改名流程
2. 增加範例資料夾與範例報表
3. 增加更完整的錯誤處理與操作提示
