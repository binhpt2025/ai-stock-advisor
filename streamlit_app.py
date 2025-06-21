import streamlit as st
import pandas as pd
import datetime
import re

# --- Mock data demo, bạn có thể thay bằng crawler thực tế ---
def fetch_stock_data():
    data = {
        "Mã CK": ["VIC", "VHM", "VPB", "SSI", "VND", "STB", "MBB", "TCB", "FPT", "HPG"],
        "Khuyến nghị": ["Mua", "Mua", "Mua", "Mua", "Bán", "Bán", "Bán", "Bán", "Mua", "Mua"],
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
    return df

# --- Gửi email (cần tích hợp email API thực tế khi triển khai) ---
def send_email(df, email_address):
    # Chỉ demo: bạn nên tích hợp SendGrid, Gmail API thật cho ứng dụng chính thức
    # Dưới đây chỉ xuất ra console
    try:
        # Format table for email (text)
        table_text = df.to_markdown(index=False)
        print(f"Đã gửi email tới {email_address} với nội dung sau:\n{table_text}")
        return True, "Gửi email thành công (demo log)."
    except Exception as e:
        return False, f"Lỗi gửi email: {e}"

# --- Kiểm tra định dạng email hợp lệ ---
def is_valid_email(email):
    if not email: return False
    # Đơn giản, chỉ kiểm tra định dạng chung
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

st.set_page_config(page_title="AI Stock Advisor", layout="wide")
st.title("Stock Advisor - BinhPT")
st.markdown("#### Tư vấn chứng khoán tự động, dữ liệu cập nhật mỗi 30p.")

# Lấy/lưu trạng thái bảng & thời gian cập nhật
if 'df' not in st.session_state:
    st.session_state['df'] = fetch_stock_data()
    st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')

# --- Thanh nhập email và nút gửi email ---
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    email_address = st.text_input("Nhập email nhận báo cáo:", key="email_input")
with c2:
    st.write("")  # căn chỉnh nút với input
    if st.button("Send email"):
        if is_valid_email(email_address):
            success, msg = send_email(st.session_state['df'].copy(), email_address)
            if success:
                st.success(msg)
            else:
                st.error(msg)
        else:
            st.warning("Vui lòng nhập đúng định dạng email.")

with c3:
    st.write("")  # căn chỉnh nút với input
    if st.button("Refresh dữ liệu"):
        st.session_state['df'] = fetch_stock_data()
        st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')
        st.success(f"Đã cập nhật lúc {st.session_state['last_update']}")

st.info(f"Cập nhật lần cuối: {st.session_state['last_update']}")

# --- Bộ lọc dữ liệu ---
filter1, filter2 = st.columns([2,2])

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

df = st.session_state['df'].copy()

# --- Áp dụng filter ---
if buy_sell_option != "Tất cả":
    df = df[df["Khuyến nghị"] == buy_sell_option]
if price_option == "> 20,000 VNĐ":
    df = df[df["Giá hiện tại"] > 20000]
elif price_option == "≤ 20,000 VNĐ":
    df = df[df["Giá hiện tại"] <= 20000]

# --- Highlight dòng Mua nhất/Bán nhất khi View All ---
def highlight_rows(row):
    if buy_sell_option == "Tất cả" and len(df) > 0:
        # Highlight Mua nhất: Giá thấp nhất trong các mã Mua
        mua_rows = df[df["Khuyến nghị"] == "Mua"]
        ban_rows = df[df["Khuyến nghị"] == "Bán"]
        style = [''] * len(row)
        if not mua_rows.empty:
            idx_mua_best = mua_rows["Giá hiện tại"].idxmin()
            if row.name == idx_mua_best:
                style = ['background-color: #b6fcb6'] * len(row)  # Xanh lá nhạt
        if not ban_rows.empty:
            idx_ban_best = ban_rows["Giá hiện tại"].idxmax()
            if row.name == idx_ban_best:
                style = ['background-color: #ffbdbd'] * len(row)  # Đỏ nhạt
        return style
    else:
        return [''] * len(row)

# --- Hiển thị bảng với style ---
st.markdown("#### Danh sách mã chứng khoán")
if df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc.")
else:
    st.dataframe(
        df.style.apply(highlight_rows, axis=1),
        use_container_width=True,
        height=430,
    )

st.caption("""
- Button **Send email** gửi bảng dữ liệu (dưới dạng markdown) đến địa chỉ email hợp lệ.
- Bạn có thể lọc dữ liệu theo Khuyến nghị (Mua/Bán) và Giá trị cổ phiếu.
- Màu **xanh lá**: mã nên Mua nhất; màu **đỏ nhạt**: mã nên Bán nhất (khi view tất cả).
- Demo này chưa gửi email thật (log ra màn hình). Để gửi email thật, bạn cần tích hợp SendGrid hoặc Gmail API trong hàm `send_email`.
""")
