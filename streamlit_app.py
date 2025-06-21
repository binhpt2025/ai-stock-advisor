import streamlit as st
import pandas as pd
import datetime
import re
import numpy as np

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- Mock data demo ---
def fetch_stock_data():
    data = {
        "Mã CK": ["VIC", "VHM", "VPB", "SSI", "VND", "STB", "MBB", "TCB", "FPT", "HPG"],
        "Khuyến nghị": ["Mua", "Mua", "Mua", "Mua", "Bán", "Bán", "Bán", "Bán", "Mua", "Mua"],
        "Giá cuối ngày hôm qua": [50900, 46000, 22800, 32100, 15200, 17400, 22800, 30900, 96500, 25800],
        "Giá hiện tại": [51200, 45700, 23400, 32500, 14700, 17100, 22300, 31400, 97800, 26500],
        "Lý do": [
            "Tăng trưởng ổn định, dòng tiền mạnh",
            "Nền tảng vững, giá hấp dẫn",
            "Lợi nhuận Q2 vượt dự báo",
            "Kỳ vọng ngành chứng khoán phục hồi",
            "Rủi ro thị trường, sức mua yếu",
            "Tăng nóng, cần điều chỉnh",
            "Chưa rõ động lực tăng giá",
            "Thị trường bất ổn, tiềm ẩn rủi ro",
            "Doanh thu công nghệ tăng mạnh",
            "Giá thép hồi phục, nhu cầu tăng"
        ]
    }
    df = pd.DataFrame(data)
    # Tính tỷ lệ thay đổi %
    df["Tỷ lệ thay đổi (Tăng/Giảm)"] = (
        (df["Giá hiện tại"] - df["Giá cuối ngày hôm qua"]) / df["Giá cuối ngày hôm qua"] * 100
    ).round(2)
    # Format hiển thị %
    df["Tỷ lệ thay đổi (Tăng/Giảm)"] = df["Tỷ lệ thay đổi (Tăng/Giảm)"].apply(
        lambda x: f"{x:+.2f}%" if not pd.isna(x) else "-"
    )
    # Đặt lại thứ tự cột
    df = df[
        ["Mã CK", "Khuyến nghị", "Giá cuối ngày hôm qua", "Giá hiện tại", "Tỷ lệ thay đổi (Tăng/Giảm)", "Lý do"]
    ]
    return df

def send_email(df, email_address):
    try:
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]

        subject = "Báo cáo khuyến nghị chứng khoán từ Stock Advisor - BinhPT"
        body = (
            "Chào bạn,\n\n"
            "Đây là bảng khuyến nghị chứng khoán mới nhất bạn vừa nhận từ ứng dụng Stock Advisor của BinhPT:\n\n"
            f"{df.to_markdown(index=False)}\n\n"
            "Trân trọng,\nAI Stock Advisor \nBinhPT"
        )

        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = email_address
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))

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

if 'df' not in st.session_state:
    st.session_state['df'] = fetch_stock_data()
    st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')
if 'filtered_df' not in st.session_state:
    st.session_state['filtered_df'] = st.session_state['df']

# --- Nhập email + nút gửi email + Refresh ---
c1, c2, c3 = st.columns([4, 1])
with c1:
    # email_address = st.text_input("Nhập email nhận báo cáo:", key="email_input") 

    email_address = st.text_input(
        "",  # Ẩn label
        placeholder="Nhập email nhận báo cáo",
        key="email_input"

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
            
    send_email_clicked = st.button("Send email", use_container_width=True)
with c3:
    st.write("")
    if st.button("Refresh dữ liệu"):
        st.session_state['df'] = fetch_stock_data()
        st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')
        st.session_state['filtered_df'] = st.session_state['df']
        st.success(f"Đã cập nhật lúc {st.session_state['last_update']}")

st.info(f"Cập nhật lần cuối: {st.session_state['last_update']}")

# --- Lọc dữ liệu (Mua/Bán, Giá cổ phiếu) + Button Query chính xác vị trí ---
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
    if price_option == "> 20,000 VNĐ":
        df = df[df["Giá hiện tại"] > 20000]
    elif price_option == "≤ 20,000 VNĐ":
        df = df[df["Giá hiện tại"] <= 20000]
    st.session_state['filtered_df'] = df

df = st.session_state['filtered_df']

# --- Highlight dòng Mua nhất/Bán nhất ---
def highlight_rows(row):
    style = [''] * len(row)
    if len(df) > 0:
        if buy_sell_option == "Tất cả":
            mua_rows = df[df["Khuyến nghị"] == "Mua"]
            ban_rows = df[df["Khuyến nghị"] == "Bán"]
            if not mua_rows.empty:
                idx_mua_best = mua_rows["Giá hiện tại"].idxmin()
                if row.name == idx_mua_best:
                    style = ['background-color: #b6fcb6'] * len(row)
            if not ban_rows.empty:
                idx_ban_best = ban_rows["Giá hiện tại"].idxmax()
                if row.name == idx_ban_best:
                    style = ['background-color: #ffbdbd'] * len(row)
        elif buy_sell_option == "Mua":
            idx_mua_best = df["Giá hiện tại"].idxmin()
            if row.name == idx_mua_best:
                style = ['background-color: #b6fcb6'] * len(row)
        elif buy_sell_option == "Bán":
            idx_ban_best = df["Giá hiện tại"].idxmax()
            if row.name == idx_ban_best:
                style = ['background-color: #ffbdbd'] * len(row)
    return style

# --- Hiển thị bảng ---
st.markdown("#### Danh sách mã chứng khoán")
if df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc.")
else:
    # Sử dụng Pandas Styler cho highlight
    st.dataframe(
        df.style.apply(highlight_rows, axis=1),
        use_container_width=True,
        height=430,
    )

st.caption("""
- Bấm **Query** để lọc dữ liệu theo các bộ lọc trên. Không bấm sẽ giữ nguyên dữ liệu cũ.
- Button **Send email** gửi bảng dữ liệu đang hiển thị đến địa chỉ email hợp lệ.
- Màu **xanh lá**: mã nên Mua nhất; **đỏ nhạt**: mã nên Bán nhất (tuỳ bộ lọc).
- Đã bổ sung các cột: "Giá cuối ngày hôm qua", "Tỷ lệ thay đổi (Tăng/Giảm)" và hiển thị đúng vị trí.
""")
