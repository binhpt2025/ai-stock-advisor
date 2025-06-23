import streamlit as st
import pandas as pd
import datetime
import re
import numpy as np
import subprocess
import os
 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
 
CSV_FILE = "stock_sentiment.csv"
CRAWL_SCRIPT = "crawl_stock_sentiment.py"
 
def fetch_stock_data():
    # Đọc dữ liệu từ file CSV
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
    else:
        # Nếu chưa có file thì trả về DataFrame rỗng
        df = pd.DataFrame(columns=["Mã CK", "Khuyến nghị", "Giá cuối ngày hôm qua", "Giá hiện tại", "Tỷ lệ thay đổi (Tăng/Giảm)", "Lý do"])
    return df
 
def run_crawl_script():
    # Chạy file crawl_stock_sentiment.py, ghi đè file CSV mới nhất
    try:
        result = subprocess.run(["python", CRAWL_SCRIPT], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return True, "Đã crawl dữ liệu mới thành công!"
        else:
            return False, f"Lỗi crawl dữ liệu: {result.stderr}"
    except Exception as e:
        return False, f"Lỗi khi chạy script crawl: {e}"
 
def send_email(df, email_address):
    try:
        # Tạo bản sao DataFrame để format mà không làm hỏng dữ liệu gốc
        df_send = df.copy()
        # Định dạng giá khi gửi email (triệu đồng, 2 chữ số thập phân)
        for col in ["Giá cuối ngày hôm qua", "Giá hiện tại"]:
            if col in df_send.columns:
                df_send[col] = df_send[col].apply(
                    lambda x: f"{float(x)/1000:.2f}" if isinstance(x, (int, float, np.integer, np.floating)) and str(x).strip() != "" else x
                )
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]
 
        subject = "Báo cáo khuyến nghị chứng khoán từ Stock Advisor - BinhPT"
 
        def highlight_rows(row):
            style = [''] * len(row)
            if len(df_send) > 0:
                if "Mua" in df_send["Khuyến nghị"].values:
                    mua_vals = pd.to_numeric(df_send[df_send["Khuyến nghị"] == "Mua"]["Giá hiện tại"], errors="coerce")
                    idx_mua_best = mua_vals.idxmin() if not mua_vals.empty else None
                    if row.name == idx_mua_best:
                        style = ['background-color: #b6fcb6'] * len(row)
                if "Bán" in df_send["Khuyến nghị"].values:
                    ban_vals = pd.to_numeric(df_send[df_send["Khuyến nghị"] == "Bán"]["Giá hiện tại"], errors="coerce")
                    idx_ban_best = ban_vals.idxmax() if not ban_vals.empty else None
                    if row.name == idx_ban_best:
                        style = ['background-color: #ffbdbd'] * len(row)
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
st.markdown("#### Tư vấn chứng khoán tự động, lọc dữ liệu & gửi email (cập nhật từ dữ liệu web)")
 
# --- Nhập email + nút gửi email + Refresh ---
c1, c2, c3 = st.columns([4, 1, 1])
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
 
with c3:
    st.write("")
    if st.button("Refresh dữ liệu"):
        with st.spinner("Đang lấy dữ liệu mới từ web, vui lòng chờ..."):
            ok, msg = run_crawl_script()
            if ok:
                st.session_state['df'] = fetch_stock_data()
                st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')
                st.session_state['filtered_df'] = st.session_state['df']
                st.success(f"{msg} (Cập nhật lúc {st.session_state['last_update']})")
            else:
                st.error(msg)
 
if 'df' not in st.session_state:
    st.session_state['df'] = fetch_stock_data()
    st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')
if 'filtered_df' not in st.session_state:
    st.session_state['filtered_df'] = st.session_state['df']
 
st.info(f"Cập nhật lần cuối: {st.session_state['last_update']}")
 
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
 
if query_clicked:
    df = st.session_state['df'].copy()
    if buy_sell_option != "Tất cả":
        df = df[df["Khuyến nghị"] == buy_sell_option]
    if price_option == "> 20,000 VNĐ":
        df = df[df["Giá hiện tại"].apply(lambda x: str(x).replace('.', '', 1).isdigit() and float(x) > 20000 if str(x).strip() != "" else False)]
    elif price_option == "≤ 20,000 VNĐ":
        df = df[df["Giá hiện tại"].apply(lambda x: str(x).replace('.', '', 1).isdigit() and float(x) <= 20000 if str(x).strip() != "" else False)]
    st.session_state['filtered_df'] = df
 
df = st.session_state['filtered_df']
 
def highlight_rows(row):
    style = [''] * len(row)
    if len(df) > 0 and "Giá hiện tại" in df.columns:
        try:
            gia_hien_tai_col = pd.to_numeric(df["Giá hiện tại"], errors="coerce")
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