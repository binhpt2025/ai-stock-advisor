import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
 
def fetch_stock_data():
    base_url = "https://cafef.vn"
    list_url = "https://cafef.vn/tai-chinh-chung-khoan.chn"
    res = requests.get(list_url, timeout=15)
    soup = BeautifulSoup(res.text, "lxml")
    articles = soup.select("h3.title-news a")
 
    result_list = []
    for a in articles[:20]:  # Crawl 20 bài mới nhất
        url = base_url + a.get("href") if a.get("href", "").startswith("/") else a.get("href")
        title = a.text.strip()
        try:
            article_res = requests.get(url, timeout=10)
            article_soup = BeautifulSoup(article_res.text, "lxml")
            body = " ".join([p.text for p in article_soup.select("div.contentdetail > p")])
        except Exception:
            body = ""
        tickers = re.findall(r"\b[A-Z]{3,5}\b", title + " " + body)
        tickers = [m for m in tickers if m not in ["HOSE", "HNX", "UPCOM", "VNINDEX"] and not m.isdigit()]
        sentiment = "Khó xác định"
        if any(w in body for w in ["khuyến nghị mua", "nên mua", "tích cực", "mục tiêu tăng", "mua vào"]):
            sentiment = "Mua"
        elif any(w in body for w in ["chốt lời", "bán ra", "áp lực bán", "giảm tỷ trọng", "cảnh báo"]):
            sentiment = "Bán"
        result_list.append({
            "url": url,
            "title": title,
            "tickers": tickers,
            "sentiment": sentiment
        })
 
    buy_counter = {}
    sell_counter = {}
    for art in result_list:
        for m in art["tickers"]:
            if art["sentiment"] == "Mua":
                buy_counter[m] = buy_counter.get(m, 0) + 1
            elif art["sentiment"] == "Bán":
                sell_counter[m] = sell_counter.get(m, 0) + 1
 
    top_buy = sorted(buy_counter.items(), key=lambda x: x[1], reverse=True)[:10]
    top_sell = sorted(sell_counter.items(), key=lambda x: x[1], reverse=True)[:10]
 
    rows = []
    for m, count in top_buy:
        rows.append({
            "Mã CK": m,
            "Khuyến nghị": "Mua",
            "Lý do": f"Có {count} bài/nguồn khuyến nghị MUA gần đây (CafeF)",
            "Giá cuối ngày hôm qua": "",
            "Giá hiện tại": "",
            "Tỷ lệ thay đổi (Tăng/Giảm)": ""
        })
    for m, count in top_sell:
        rows.append({
            "Mã CK": m,
            "Khuyến nghị": "Bán",
            "Lý do": f"Có {count} bài/nguồn khuyến nghị BÁN gần đây (CafeF)",
            "Giá cuối ngày hôm qua": "",
            "Giá hiện tại": "",
            "Tỷ lệ thay đổi (Tăng/Giảm)": ""
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[["Mã CK", "Khuyến nghị", "Giá cuối ngày hôm qua", "Giá hiện tại", "Tỷ lệ thay đổi (Tăng/Giảm)", "Lý do"]]
    return df
 
if __name__ == "__main__":
    df = fetch_stock_data()
    # Xuất ra file CSV (ghi đè, không hỏi lại)
    df.to_csv("stock_sentiment.csv", index=False, encoding='utf-8-sig')
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Đã crawl & lưu dữ liệu vào stock_sentiment.csv ({len(df)} dòng)")