這是一份根據您的 PRD 內容，專為初學者與快速驗證設計的 **AI 智慧客服問題管理系統 (AI-Powered CS Issue Tracker) 系統設計文件 (SDD)**。

---

# 系統設計文件 (SDD)：AI 智慧客服問題管理系統

**版本：** v1.0  
**狀態：** 實作準備  
**針對對象：** 初學者、AI 輔助開發、MVP 快速驗證  

---

## 1. 簡介

### 1.1 專案概述
本專案旨在開發一個輕量級的 AI 客服問題管理平台。透過整合大型語言模型 (LLM)，將來自 Email、Line 或 PDF 的雜亂客服資訊自動結構化為可管理的案件，並提供視覺化看板與自動化回覆功能，以解決資訊碎片化與追蹤難度高的問題。

### 1.2 系統目標
*   **數據自動化**：利用 AI 減少 70% 以上的手動資料輸入時間。
*   **集中管理**：提供單一入口彙整所有管道的客服需求。
*   **流程透明**：透過看板 (Kanban) 即時追蹤案件進度與負責人。
*   **溝通加速**：AI 自動生成專業回覆草稿，並與 Outlook 連動。
*   **快速部署**：基於 Python 生態系，支援本機環境快速執行與驗證。

### 1.3 技術選型
*   **程式語言**：Python 3.10+
*   **Web UI 框架**：**Streamlit** (選用原因：開發速度最快，內建多種 UI 組件，適合數據密集型應用)
*   **資料庫**：**SQLite** (選用原因：單一檔案免安裝，適合 MVP 與本機測試)
*   **資料庫 ORM**：**SQLAlchemy** (選用原因：標準化資料操作，未來易於遷移至 PostgreSQL)
*   **AI 核心**：OpenAI API (GPT-4o)
*   **PDF 處理**：PyMuPDF (fitz) 或 pdfplumber

---

## 2. 系統架構與運作流程

### 2.1 整體架構
本系統採用全棧式單體架構，專注於本機運行效率：

```
[使用者瀏覽器] <--> [Streamlit 介面層] <--> [業務邏輯層 (Python)] <--> [數據持久層 (SQLAlchemy + SQLite)]
                                          |
                                          +--> [外部服務 (OpenAI API / MS Graph API)]
```

### 2.2 運作流程詳解
1.  **資料輸入**：客服人員在 Streamlit 介面貼入文字或上傳 PDF。
2.  **AI 解析**：系統調用 OpenAI API，解析非結構化文字，提取客戶名、產品號及摘要。
3.  **案件確認**：人員校對 AI 提取的資料並選擇負責人後，點擊「存檔」。
4.  **數據存儲**：SQLAlchemy 將資料寫入 `issues.db` (SQLite)。
5.  **狀態追蹤**：主管在「看板頁面」透過拖拉或選單變更案件狀態。
6.  **結案回覆**：AI 根據處理紀錄生成回覆，人員點擊「傳送至 Outlook」開啟草稿。

---

## 3. 核心模組設計

本系統將分為以下核心模組：

1.  **`models.py` (資料模型模組)**：定義 SQLAlchemy 資料表結構。
2.  **`database.py` (資料庫引擎)**：處理資料庫連接、Session 管理及 CRUD 基本操作。
3.  **`ai_service.py` (AI 邏輯模組)**：封裝 OpenAI API 調用，處理 Prompt 工程與內容解析。
4.  **`outlook_service.py` (外部整合模組)**：處理郵件草稿生成邏輯。
5.  **`app.py` (主程式與 UI 模組)**：Streamlit 進入點，負責頁面渲染與用戶互動。

---

## 4. 資料庫設計

### 4.1 資料庫選型
使用 **SQLite**，因其無須設定 Server，且能完整支援本系統所需之關聯查詢。

### 4.2 資料表設計

#### 資料表：`issues` (案件表)
| 欄位名稱 | 資料型態 | 說明 | 備註 |
|----------|----------|------|------|
| id | INTEGER | 唯一識別碼 | 主鍵，自動遞增 |
| customer_name | VARCHAR | 客戶名稱 | AI 提取或手動輸入 |
| product_id | VARCHAR | 產品編號 | AI 提取 |
| summary | TEXT | 問題摘要 | AI 提取 |
| raw_content | TEXT | 原始輸入內容 | 備查用 |
| status | VARCHAR | 案件狀態 | 待處理/處理中/已解決 |
| priority | VARCHAR | 優先級 | 高/中/低 |
| agent_id | INTEGER | 負責人 ID | 關聯至 users.id |
| due_date | DATE | 預計結案日期 | AI 建議或手動 |
| created_at | DATETIME | 建立時間 | 自動生成 |

#### 資料表：`users` (用戶表)
| 欄位名稱 | 資料型態 | 說明 | 備註 |
|----------|----------|------|------|
| id | INTEGER | 用戶 ID | 主鍵 |
| name | VARCHAR | 姓名 | 客服人員姓名 |
| email | VARCHAR | 電子郵件 | 用於 Outlook 關聯 |

---

## 5. 使用者介面與互動規劃

### 5.1 頁面結構 (Sidebar 導航)
*   **📊 管理儀表板 (Dashboard)**：顯示圓餅圖與負荷統計。
*   **📥 新增案件 (New Issue)**：包含文字框、檔案上傳與 AI 解析結果確認。
*   **📋 案件中心 (Issue List)**：表格形式的所有案件列表。
*   **🧱 視覺化看板 (Kanban)**：三欄式狀態拖拉視圖。

### 5.2 核心互動流程
1.  **進入「新增案件」** -> 貼入 Line 訊息 -> 點擊「AI 預析」。
2.  **AI 解析結果**會自動填入下方的輸入欄位。
3.  **點擊「建立案件」** -> 系統提示成功並轉向「案件中心」。
4.  **在「看板」中** -> 點擊卡片 -> 選擇「生成回覆草稿」 -> 跳轉至 Outlook 介面。

---

## 6. API 設計 / 功能函數

### 6.1 `ai_service.py`
*   **函數**：`analyze_issue_content(text: str) -> dict`
    *   **職責**：將 raw text 傳給 GPT-4o，要求返回 JSON 格式的結構化資料。
*   **函數**：`generate_email_draft(issue_details: dict) -> str`
    *   **職責**：根據處理結果生成專業回覆文案。

### 6.2 `database.py`
*   **函數**：`get_all_issues()`、`create_issue(data)`、`update_issue_status(id, status)`
    *   **職責**：執行 SQL 指令並返回結果物件。

---

## 7. 錯誤處理策略

| 錯誤情境 | 處理策略 | UI 呈現 |
|----------|----------|------|
| OpenAI API 金鑰失效 | 捕捉 Exception，切換為手動輸入模式 | 顯示紅色警告 Alert：「AI 服務暫不可用」 |
| 資料庫寫入失敗 | 使用 try-except 回滾 Session | 彈出錯誤通知，保留用戶已輸入內容 |
| PDF 無法解析 | 提示檔案損壞或格式不符 | 顯示訊息：「請嘗試手動貼入文字內容」 |

---

## 8. 實作路徑 (Implementation Roadmap)

### 8.1 環境建置與依賴安裝
```bash
# 建立專案
mkdir ai_cs_tracker
cd ai_cs_tracker
python -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate # Windows

# 建立 requirements.txt
cat <<EOT > requirements.txt
streamlit
sqlalchemy
pandas
openai
python-dotenv
pycryptodome
EOT

pip install -r requirements.txt
```

### 8.2 資料庫模組開發 (`models.py`)
1.  定義 `Base` 類別。
2.  定義 `Issue` 與 `User` 類別及其欄位。
3.  實作 `init_db()` 函數用於初始化 `.db` 檔案。

### 8.3 AI 業務邏輯開發 (`ai_service.py`)
1.  設定 OpenAI Client。
2.  撰寫 System Prompt (例如："你是一個專業客服助理，請從以下文字提取 JSON...")。
3.  實作 `extract_info` 函數。

### 8.4 使用者介面開發 (`app.py`)
1.  實作 `st.sidebar` 導航。
2.  **儀表板頁面**：使用 `st.columns` 顯示數據指標，`st.plotly_chart` (或 Streamlit 內建圖表) 顯示分布。
3.  **新增案件頁面**：實作 `st.text_area` 與 `st.form`。
4.  **看板頁面**：利用 `st.expander` 模擬卡片。

### 8.5 測試與驗證
1.  **功能測試**：確保貼入文字後，AI 欄位能正確自動填充。
2.  **流程測試**：確認狀態變更後，資料庫中的 `status` 欄位同步更新。

### 8.6 部署與運行說明
1.  在根目錄建立 `.env` 檔案並填入 `OPENAI_API_KEY`。
2.  執行指令：
```bash
streamlit run app.py
```

---

## 9. 附錄：AI 提示詞參考 (Prompt)
針對欄位擷取，建議使用以下 Prompt 結構：
> "你是一個客服資料結構化專家。請分析以下訊息，並僅以 JSON 格式回傳。欄位包含：customer_name, product_id, summary (50字內), priority (High/Medium/Low), due_date (YYYY-MM-DD)。訊息內容：{user_input}"

---

此 SDD 提供了清晰的開發路徑，讓開發者能專注於 Python 邏輯與 AI 提示詞的優化，而無需處理複雜的環境配置。