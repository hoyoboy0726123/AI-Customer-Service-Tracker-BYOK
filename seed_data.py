import random
from datetime import datetime, timedelta
from database import SessionLocal, init_db
from models import Issue, User

# 初始化資料庫與人員
init_db()
db = SessionLocal()

# 清空現有案件 (為了重新注入高品質數據)
db.query(Issue).delete()
db.commit()

# 確保有客服人員
users = db.query(User).all()
if not users:
    print("錯誤：請先執行 app.py 初始化人員資料。")
    exit()
user_ids = [u.id for u in users]

customers = ["台積電", "鴻海", "聯發科", "華碩", "宏碁", "微星", "廣達", "仁寶", "大立光", "欣興電子", "日月光", "南亞科"]
products = ["MB-100", "CPU-X2", "GPU-RTX", "RAM-DDR5", "SSD-M2", "POWER-850W", "CASE-MESH", "FAN-RGB", "SERVER-Z1"]
statuses = ["待處理", "處理中", "已解決"]
priorities = ["高", "中", "低"]
people = ["張大明", "李小華", "王組長", "陳經理", "趙工程師", "孫小姐", "周技術員", "吳廠長"]

# 原始訊息模板
raw_templates = [
    "【Line 轉發】{person}：我們公司的 {prod} 突然壞了，地址在 {addr}，急件請聯絡分機 {ext}。預計希望 {due} 前修好。",
    "寄件者：{person} <{person_en}@company.com>\n收件者：客服部\n主旨：報修請求 - {prod}\n\n內容：我們廠區的 {prod} 出現異常，目前暫停運作。請派人到 {addr} 檢查。聯絡電話：02-2345-6789 #{ext}。",
    "電話紀錄紀錄人：系統管理員\n來電者：{person} ({cust})\n反映問題：{prod} 運作不穩。\n備註：客戶聽起來很急，要求 {due} 必須結案。地址已確認為：{addr}。",
    "【系統自動報警】\n設備編號：{prod}\n所屬單位：{cust}\n錯誤代碼：ERR-999\n偵測時間：{now}\n請儘速指派人員處理。客戶聯絡人：{person}，分機 {ext}。"
]

addresses = ["新竹科學園區研發路1段", "台南科學園區南科三路", "台中工業區五路", "桃園龜山工業區", "台北內湖科學園區"]

print("正在重新生成 50 筆高品質模擬數據 (包含詳細原始訊息)...")

for i in range(50):
    cust = random.choice(customers)
    prod = random.choice(products)
    prio = random.choice(priorities)
    stat = random.choice(statuses)
    person = random.choice(people)
    addr = random.choice(addresses)
    ext = random.randint(100, 999)
    
    # 日期計算
    due_date_obj = (datetime.now() + timedelta(days=random.randint(-5, 15))).date()
    created_at = datetime.now() - timedelta(days=random.randint(1, 20))
    
    # 產生原始訊息
    raw_content = random.choice(raw_templates).format(
        person=person, person_en=person.lower(), prod=prod, cust=cust, 
        addr=addr, ext=ext, due=due_date_obj, now=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    
    # 產生摘要 (簡短版)
    summary = f"客戶反映 {prod} 異常。由 {person} 報修，地址位於 {addr}。需要分機 {ext} 聯繫。"

    issue = Issue(
        customer_name=f"{cust} - {random.randint(1, 3)}廠",
        product_id=prod,
        summary=summary,
        raw_content=raw_content,
        status=stat,
        priority=prio,
        due_date=due_date_obj,
        created_at=created_at,
        agent_id=random.choice(user_ids)
    )
    db.add(issue)

db.commit()
db.close()
print("數據注入完成！現在每筆案件都擁有詳細的「原始訊息」可供查看。")
