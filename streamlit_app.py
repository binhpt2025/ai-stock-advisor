import streamlit as st
import pandas as pd
import datetime
import re

# --- Mock data demo ---
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
    return pd.DataFrame(data)

def send_email(df, email_address):
    # Demo function, không gửi email thực
    try:
        table_text = df.to_markdown(index=False)
        print(f"Đã gửi email tới {email_address} với nội dung sau:\n{table_text}")
        return True, "Gửi email thành công (demo log)."
    except Exception as e:
        return False, f"Lỗi gửi email: {e}"

def is_valid_email(email):
    if not email: return False
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

st.set_page_config(page_title="AI Stock Advisor", layout="wide")
st.title("Stock Advisor - BinhPT")
st.markdown("#### Tư vấn chứng khoán tự động, gửi dữ liệu đến email (mỗi 30p)")

if 'df' not in st.session_state:
    st.session_state['df'] = fetch_stock_data()
    st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')

# --- Nhập email + nút gửi email + Refresh ---
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    email_address = st.text_input("Nhập email nhận báo cáo:", key="email_input")
with c2:
    st.write("")  # căn chỉnh nút với input
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
        st.session_state['df'] = fetch_stock_data()
        st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')
        st.session_state['filtered_df'] = st.session_state['df']
        st.success(f"Đã cập nhật lúc {st.session_state['last_update']}")

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

# --- Áp dụng filter chỉ khi bấm Query (lưu kết quả vào session_state['filtered_df']) ---
if 'filtered_df' not in st.session_state:
    st.session_state['filtered_df'] = st.session_state['df']

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
            # Highlight mã Mua giá thấp nhất
            idx_mua_best = df["Giá hiện tại"].idxmin()
            if row.name == idx_mua_best:
                style = ['background-color: #b6fcb6'] * len(row)
        elif buy_sell_option == "Bán":
            # Highlight mã Bán giá cao nhất
            idx_ban_best = df["Giá hiện tại"].idxmax()
            if row.name == idx_ban_best:
                style = ['background-color: #ffbdbd'] * len(row)
    return style

# --- Hiển thị bảng ---
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
- Bấm **Query** để lọc dữ liệu theo các bộ lọc trên. Không bấm sẽ giữ nguyên dữ liệu cũ.
- Button **Send email** gửi bảng dữ liệu đang hiển thị đến địa chỉ email hợp lệ.
- Màu **xanh lá**: mã nên Mua nhất; **đỏ nhạt**: mã nên Bán nhất (tuỳ bộ lọc).
""")
