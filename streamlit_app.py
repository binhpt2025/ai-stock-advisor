import streamlit as st
import pandas as pd
import datetime
import re
import numpy as np

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

def fetch_stock_data():
    base_url = "https://cafef.vn"
    list_url = "https://cafef.vn/tai-chinh-chung-khoan.chn"
    res = requests.get(list_url, timeout=15)
    soup = BeautifulSoup(res.text, "lxml")
    articles = soup.select("h3.title-news a")
    result_list = []
    for a in articles[:20]:
        url = base_url + a.get("href") if a.get("href", "").startswith("/") else a.get("href")
        title = a.text.strip()
        # Lấy nội dung bài viết
        try:
            article_res = requests.get(url, timeout=10)
            article_soup = BeautifulSoup(article_res.text, "lxml")
            body = " ".join([p.text for p in article_soup.select("div.contentdetail > p")])
        except Exception:
            body = ""
        # Tìm các mã cổ phiếu trong title + body (viết hoa 3-5 ký tự)
        tickers = re.findall(r"\b[A-Z]{3,5}\b", title + " " + body)
        tickers = [m for m in tickers if m not in ["HOSE", "HNX", "UPCOM", "VNINDEX"] and not m.isdigit()]
        # Phân tích sentiment đơn giản
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

    # Tổng hợp tần suất các mã được khuyến nghị Mua/Bán
    buy_counter = {}
    sell_counter = {}
    for art in result_list:
        for m in art["tickers"]:
            if art["sentiment"] == "Mua":
                buy_counter[m] = buy_counter.get(m, 0) + 1
            elif art["sentiment"] == "Bán":
                sell_counter[m] = sell_counter.get(m, 0) + 1

    # Lấy top 10 Mua và Bán
    top_buy = sorted(buy_counter.items(), key=lambda x: x[1], reverse=True)[:10]
    top_sell = sorted(sell_counter.items(), key=lambda x: x[1], reverse=True)[:10]

    # Chuẩn hóa output thành DataFrame
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
    # Debug: xem đã lấy được bao nhiêu dòng
    print(f"DEBUG: fetch_stock_data returning {df.shape[0]} rows")
    return df

def send_email(df, email_address):
    try:
        df_send = df.copy()
        for col in ["Giá cuối ngày hôm qua", "Giá hiện tại"]:
            if col in df_send.columns:
                df_send[col] = df_send[col].apply(
                    lambda x: f"{float(x)/1000:.2f}" if isinstance(x, (int, float, np.integer, np.floating)) and x else x
                )
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]
        subject = "Báo cáo khuyến nghị chứng khoán từ Stock Advisor - BinhPT"
        def highlight_rows(row):
            style = [''] * len(row)
            if len(df_send) > 0 and "Giá hiện tại" in df_send.columns:
                try:
                    gia_hien_tai_col = df_send["Giá hiện tại"].apply(lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else np.nan)
                    if "Mua" in df_send["Khuyến nghị"].values:
                        idx_mua_best = gia_hien_tai_col[df_send["Khuyến nghị"]=="Mua"].idxmin()
                        if row.name == idx_mua_best:
                            style = ['background-color: #b6fcb6'] * len(row)
                    if "Bán" in df_send["Khuyến nghị"].values:
                        idx_ban_best = gia_hien_tai_col[df_send["Khuyến nghị"]=="Bán"].idxmax()
                        if row.name == idx_ban_best:
                            style = ['background-color: #ffbdbd'] * len(row)
                except Exception:
                    pass
            return style
        html_table = (
            df_send.style
            .apply(highlight_rows, axis=1)
            .set_table_attributes(
                'border="1" cellpadding="4" cellspacing="0" style="border-collapse: collapse; font-family: Arial; font-size: 14px"'
            )
            .hide(axis="index")
            .to_html()
        )
        body = f"""
        <p>Chào bạn,<br><br>
        Dưới đây là bảng khuyến nghị chứng khoán mới nhất mà BinhPT gửi đến bạn nhé:<br></p>
        {html_table}
        <br><br>Trân trọng,<br>AI Stock Advisor,<br>BinhPT
        """
        message = MIMEMultipart("alternative")
        message["From"] = sender
        message["To"] = email_address
        message["Subject"] = subject
        message.attach(MIMEText(body, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, email_address, message.as_string())
        return True, f"Đã gửi email thành công tới {email_address}!"
    except Exception as e:
        return False, f"Lỗi gửi email: {e}"

def is_valid_email(email):
    if not email: return False
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

st.set_page_config(page_title="AI Stock Advisor", layout="wide")
st.title("Stock Advisor - BinhPT")
st.markdown("#### Tư vấn chứng khoán tự động, lọc dữ liệu & gửi email (mỗi 30p)")

# === Khởi tạo, Refresh và lọc bộ nhớ session_state ===
if 'last_update' not in st.session_state:
    st.session_state['last_update'] = None

# --- Nút Refresh: luôn lấy data mới ---
if st.session_state['last_update'] is None or st.button("Refresh dữ liệu"):
    st.session_state['df'] = fetch_stock_data()
    st.session_state['filtered_df'] = st.session_state['df']
    st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')
st.info(f"Cập nhật lần cuối: {st.session_state['last_update']}")

# --- Nhập email + nút gửi email ---
c1, c2 = st.columns([5, 1])
with c1:
    email_address = st.text_input("Nhập email nhận báo cáo:", key="email_input") 
with c2:
    st.write("")
    if st.button("Send email"):
        if is_valid_email(email_address):
            success, msg = send_email(st.session_state.get('filtered_df', st.session_state['df']).copy(), email_address)
            if success:
                st.success(msg)
            else:
                st.error(msg)
        else:
            st.warning("Vui lòng nhập đúng định dạng email.")

# --- Lọc dữ liệu (Mua/Bán, Giá cổ phiếu) + Button Query ---
filter1, filter2, filter3 = st.columns([2,2,1])
with filter1:
    buy_sell_option = st.selectbox(
        "Lọc theo khuyến nghị:",
        options=["Tất cả", "Mua", "Bán"],
        index=0,
        key="filter_buy_sell"
    )
with filter2:
    price_option = st.selectbox(
        "Lọc theo giá cổ phiếu:",
        options=["Tất cả", "> 20,000 VNĐ", "≤ 20,000 VNĐ"],
        index=0,
        key="filter_price"
    )
with filter3:
    query_clicked = st.button("Query")

# --- Chỉ áp dụng filter khi bấm Query ---
if query_clicked:
    df = st.session_state['df'].copy()
    if buy_sell_option != "Tất cả":
        df = df[df["Khuyến nghị"] == buy_sell_option]
    # Chỉ filter theo giá nếu giá là số
    if price_option == "> 20,000 VNĐ":
        df = df[df["Giá hiện tại"].apply(lambda x: (str(x).replace('.', '', 1).isdigit() and float(x) > 20000))]
    elif price_option == "≤ 20,000 VNĐ":
        df = df[df["Giá hiện tại"].apply(lambda x: (str(x).replace('.', '', 1).isdigit() and float(x) <= 20000))]
    st.session_state['filtered_df'] = df

df = st.session_state['filtered_df']

def highlight_rows(row):
    style = [''] * len(row)
    if len(df) > 0 and "Giá hiện tại" in df.columns:
        try:
            gia_hien_tai_col = df["Giá hiện tại"].apply(lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else np.nan)
            if buy_sell_option == "Tất cả":
                mua_rows = df[df["Khuyến nghị"] == "Mua"]
                ban_rows = df[df["Khuyến nghị"] == "Bán"]
                if not mua_rows.empty:
                    idx_mua_best = gia_hien_tai_col[mua_rows.index].idxmin()
                    if row.name == idx_mua_best:
                        style = ['background-color: #b6fcb6'] * len(row)
                if not ban_rows.empty:
                    idx_ban_best = gia_hien_tai_col[ban_rows.index].idxmax()
                    if row.name == idx_ban_best:
                        style = ['background-color: #ffbdbd'] * len(row)
            elif buy_sell_option == "Mua":
                idx_mua_best = gia_hien_tai_col.idxmin()
                if row.name == idx_mua_best:
                    style = ['background-color: #b6fcb6'] * len(row)
            elif buy_sell_option == "Bán":
                idx_ban_best = gia_hien_tai_col.idxmax()
                if row.name == idx_ban_best:
                    style = ['background-color: #ffbdbd'] * len(row)
        except Exception:
            pass
    return style

# --- Định dạng giá trên giao diện (triệu đồng, 2 chữ số thập phân) ---
display_df = df.copy()
for col in ["Giá cuối ngày hôm qua", "Giá hiện tại"]:
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(lambda x: f"{float(x)/1000:.2f}" if str(x).replace('.', '', 1).isdigit() else x)
        
st.markdown("#### Danh sách mã chứng khoán")
if display_df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc.")
else:
    st.dataframe(
        display_df.style.apply(highlight_rows, axis=1),
        use_container_width=True,
        height=430,
    )

st.caption("""
- Bấm **Query** để lọc dữ liệu theo các bộ lọc trên. Không bấm sẽ giữ nguyên dữ liệu cũ.
- Button **Send email** gửi bảng dữ liệu đang hiển thị đến địa chỉ email hợp lệ.
- Màu **xanh lá**: mã nên Mua nhất; **đỏ nhạt**: mã nên Bán nhất (tuỳ bộ lọc).
- Đã bổ sung các cột: "Giá cuối ngày hôm qua", "Tỷ lệ thay đổi (Tăng/Giảm)" và hiển thị đúng vị trí.
""")