# Frontend Design Skill — Function Spec

## Function Spec（功能規格）

| 項目 | 內容 |
|------|------|
| **Name** | `frontend-design` |
| **License** | Complete terms in LICENSE.txt |
| **Description** | Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults. |
| **適用情境** | 當你要建立新 UI 或改造現有界面，且希望設計有獨特個性、避免模板化外觀時 |
| **檔案位置** | `~/.pi/agent/skills/frontend-design/SKILL.md` |

## User Guide（使用指南）

### 核心定位
把自己當成一家精品小工作室的設計主管——為每個客戶打造「一看就知道不是別人作品」的視覺識別。客戶已經拒絕過模板化提案，付錢買的是明確、有主張的設計觀點。

### 1. 扎根於主題（Ground it in the subject）
- 如果 brief 沒說清楚產品/主题是什麼，就先自己確定它：點出一個具體主題、目標受眾、以及這個頁面唯一的任務。
- 善用記憶中關於使用者偏好、專案背景、過往設計作為線索。
- 從主題自己的世界（材料、工具、器物、語彙）中提煉獨特選擇。

### 2. 設計原則
- **頭版就是一個論點（hero is a thesis）**：用最具有主題特徵的東西開場。大數字 + 小標籤 + 漸層是模板答案，除非真的是最佳選項，否則不用。
- **字體承載個性**：刻意搭配展示字體與正文字體，不要用到其他專案的預選字體；設定有重點的字型比例。
- **結構即資訊**：編號、分隔線、標籤應傳達內容真相，而不是純粹裝飾。例如 01/02/03 編號只在內容確實是序列時才用。
- **刻意運用動效**：頁面載入、滾動揭示、hover 微互動、氛圍動畫——整體 orchestrated 的時刻勝過零散效果；但有時少即是多。
- **複雜度匹配遠景**：極繁方向要精緻執行；簡潔方向要精準的間距、字體、細節。

### 3. 工作流程（兩遍法）
- **第一遍：brainstorm → 設計計畫**
  - **Color**：4–6 個命名的 hex 色值。
  - **Type**：2+ 種用途的字體（有性格、克制使用的展示字體 + 搭配正文字體 + 必要時的 utility 字體）。
  - **Layout**：用一散文 + ASCII 線框圖來概念化並比較。
  - **Signature**：這將被記住的那一個獨特元素。
- **第二遍：review → critique → build**
  - 審查計畫是否讀起來像對任何類似頁面都會產生的通用預設。若是，就修改並說明為什麼。
  - 確認相對獨特性後，才寫程式碼，嚴格遵循計畫，所有色彩與字體決定都從中推導。
  - ⚠️ 注意 CSS selector 的 specificity，避免 `.section` 與 `.cta` 此類選相互抵消（尤其 section 間 padding/margin）。

### 4. 常見 AI 模板三聯（要避開）
1. 暖色背景（近 `#F4F1EA`）+ 高對比 serif 展示 + terracotta 強調色
2. 近黑背景 + 單一亮綠/朱紅強調色
3. 報刊風格 + hairline 細線 + 零圓角 + 密集報刊欄

> brief 已指定這些外觀之一時，嚴格遵循（brief 的話永遠優先）。brief 留有自由度時，不要把自由花在這三個預設上。

### 5. 克制與自我批評
- **把大獨花在一個地方**：讓 signature 元素成為唯一記憶點，其餘保持安靜、簡潔，砍掉任何不服務於 brief 的裝飾。
- 建立品質底線但不聲張：響應式到手機、可見鍵盤焦點、尊重 reduced motion。
- 邊做邊批評，環境支持的話截圖（一張圖勝過千詞）。
- 香奈兒原則：出門前照鏡子，摘掉一個配飾。

### 6. 寫作（設計中的文案）
- 文字是設計素材，不是裝飾。動機同間距與色彩。
- 從使用者角度看：用人控制/認得出的東西命名（管理通知而非 webhook 設定）。
- 主動語態：控制項要說清效果——Save changes 而非 Submit；動詞名稱全程一致。
- 失敗與空狀態是引導機會：解釋錯在哪、怎麼修，不道歉、不含糊。
- 語氣口語化、句子大小寫、無廢話、與品牌和受眾匹配。讓每個元素只做一份工作。
