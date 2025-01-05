# 計算機組織期末專題

MipsPipeline

## 環境設置

- Python 3.12.1

# quick star

py src\main.py

## 執行步驟

- 將input 資料放入 src 中 命名為 test{ID}.txt
- 在 main.py Line 336 修改 ID
- cd src
- python main.py
- 將輸出在 src 中的 test{ID}.txt

---

# 專案報告

## 工作分配

輸出格式: Siroku
Pipline、stall、forwarding: 西瓜
Data hazard、Predict not taken: 企鵝

- 1
- 1115530 劉柏均(SiroKu1006):處理輸入、輸出和部分stall
- 3
- 4

## 遭遇的問題

1. pipeline無法以正常順序運行，state的轉換遇到問題使所有的instruction都卡在ID。  
2. Forwarding還要細分成beq和其他的Forwarding，beq要在ID階段進行並慢一個cycle，很常實作出一個功能後前面的測資就壞掉了。  
3. beq和lw的stall，有時候條件成立了但是就是不跳轉，或是直接忽略了data hazard，尤其是test3的lw和beq要進行兩個stall卡最久，因為lw特別的要在mem才獲取資料，和beq需要提前在id進行計算。  
4. beq無限迴圈的問題，因為pipeline要在各個階段傳遞，然後做完基礎的pipeline後為了時做stall或是beq造成無限迴圈，beq直接卡在ID階段然後卡死。  

## 個人心得

- 1
- 1115530 劉柏均(SiroKu1006)：這次專題讓我體驗到MIPS的可怕之處，搞了一個下午只弄好一個簡單的小功能，為了修data hazard花了很多時間，最後還是靠我的組員把他修好，我好愛他。
- 3
- 4
