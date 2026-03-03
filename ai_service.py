import os
import json
from google import genai
from groq import Groq
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class IssueAnalysis(BaseModel):
    customer_name: str
    product_id: str
    summary: str
    priority: str  # 高, 中, 低
    due_date: str  # YYYY-MM-DD

class AIService:
    def __init__(self):
        # 預設供應商
        self.provider = "gemini"
        self.gemini_client = None
        self.groq_client = None
        
        # 預設模型名稱
        self.gemini_model = "gemini-3-flash-preview"
        self.groq_model = "openai/gpt-oss-120b"

    def update_keys(self, gemini_key: str = None, groq_key: str = None):
        """
        動態更新金鑰並初始化 Client
        """
        if gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=gemini_key)
            except:
                self.gemini_client = None
        
        if groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
            except:
                self.groq_client = None

    def set_provider(self, provider_name: str):
        self.provider = provider_name.lower()

    def is_provider_ready(self) -> bool:
        """
        檢查目前選擇的供應商是否已設定金鑰
        """
        if self.provider == "groq":
            return self.groq_client is not None
        return self.gemini_client is not None

    def analyze_issue(self, text: str) -> IssueAnalysis:
        if not self.is_provider_ready():
            return None

        prompt = f"""
        你是一個專業客服助理。請從以下非結構化的客服訊息中提取關鍵資訊。
        如果資訊缺失，請根據內容推斷或填寫「未知」。
        
        訊息內容：
        {text}
        
        請嚴格按照以下 JSON 格式回傳，不要有額外文字：
        {{
            "customer_name": "客戶名稱",
            "product_id": "產品編號或序號",
            "summary": "核心問題摘要 (50字內)",
            "priority": "高/中/低 (擇一)",
            "due_date": "YYYY-MM-DD"
        }}
        """

        if self.provider == "groq" and self.groq_client:
            return self._analyze_via_groq(prompt)
        elif self.gemini_client:
            return self._analyze_via_gemini(text)
        return None

    def _analyze_via_gemini(self, text: str) -> IssueAnalysis:
        prompt = f"你是一個專業客服助理。請從以下訊息提取 JSON：{text}"
        try:
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': IssueAnalysis,
                }
            )
            return response.parsed
        except:
            return None

    def _analyze_via_groq(self, prompt: str) -> IssueAnalysis:
        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return IssueAnalysis(**data)
        except:
            return None

    def generate_reply(self, issue_details: dict) -> str:
        if not self.is_provider_ready():
            return "錯誤：未輸入 API 金鑰，無法生成回覆。"

        prompt = f"撰寫專業客服回覆：客戶 {issue_details.get('customer_name')}, 產品 {issue_details.get('product_id')}, 問題 {issue_details.get('summary')}。"
        try:
            if self.provider == "groq":
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model, messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            else:
                response = self.gemini_client.models.generate_content(model=self.gemini_model, contents=prompt)
                return response.text
        except:
            return "生成失敗，請檢查金鑰權限。"
