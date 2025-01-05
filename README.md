# 計算機組織期末專題

MipsPipeline

## 環境設置

- Python 3.12.1

# quick star

py src\main.py

## 執行步驟

- 將 input 資料放入 src 中 命名為 test{ID}.txt
- 在 main.py Line 336 修改 ID
- cd src
- python main.py
- 將輸出在 src 中的 test{ID}.txt

---

# 專案報告

## 工作分配

  劉沛辰(西瓜)：處理 pipeline、stall、forwarding
  劉柏均(SiroKu1006)：處理輸入、輸出、測試檢查是否符合預期
  錢昱名(企鵝)：處理 data hazard、Predict not taken
  朱俊傑(Jaxx)：收尾檢查 bug 丶代碼格式美化

## 遭遇的問題

1. pipeline 無法以正常順序運行，state 的轉換遇到問題使所有的 instruction 都卡在 ID。
2. Forwarding 還要細分成 beq 和其他的 Forwarding，beq 要在 ID 階段進行並慢一個 cycle，很常實作出一個功能後前面的測資就壞掉了。
3. beq 和 lw 的 stall，有時候條件成立了但是就是不跳轉，或是直接忽略了 data hazard，尤其是 test3 的 lw 和 beq 要進行兩個 stall 卡最久，因為 lw 特別的要在 mem 才獲取資料，和 beq 需要提前在 id 進行計算。
4. beq 無限迴圈的問題，因為 pipeline 要在各個階段傳遞，然後做完基礎的 pipeline 後為了時做 stall 或是 beq 造成無限迴圈，beq 直接卡在 ID 階段然後卡死。

## 個人心得

### A1115513 劉沛辰(watermelon0725)

- A1115513 劉沛辰(peipei930725):這專題真的很恐怖，瘋狂 debug，原先以為就是模擬一個 MIPS 有多難，以為就是簡單的有限狀態機的實作，但是 stall 和 forwarding 產生的蝴蝶效應讓我卡超級久，一個 stall 會影響到所有的 instructions，然後還要注意有沒有 data hazard，還有 beq 和,lw 的狀態處理，雖然很難寫，遇到的問題很多，也很謝謝 gpt 和組員的幫忙，不然我會寫到崩潰。

### 1115530 劉柏均(SiroKu1006)

- 這次專題讓我體驗到 MIPS 的可怕之處，搞了一個下午只弄好一個簡單的小功能，為了修 data hazard 花了很多時間，最後還是靠我的組員把他修好，我好愛他。

### A1115531 錢昱名(penguin72487)

我寫這個壓力好大，好難寫，寫了這個才真的了解data hazard發生在哪? Forwarding是在哪裡。
  
### A1115530 劉柏均(SiroKu1006)

這次專題讓我體驗到MIPS的可怕之處，搞了一個下午只弄好一個簡單的小功能，為了修data hazard花了很多時間，最後還是靠我的組員把他修好，我好愛他。
