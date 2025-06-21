import streamlit as st
import pandas as pd
import datetime

def fetch_stock_data():
    data = {
        "Mã CK": ["VIC", "VHM", "VPB", "SSI", "VND", "STB", "MBB", "TCB", "FPT", "HPG"],
        "Khuyến nghị": ["Mua", "Mua", "Mua", "Mua", "Bán", "Bán", "Bán", "Bán", "Mua", "Mua"],
        "Giá hiện tại": [51.2, 45.7, 23.4, 32.5, 14.7, 17.1, 22.3, 31.4, 97.8, 26.5],
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

def send_email(df, email_address):
    # Demo: In ra log thay vì gửi thật
    print(f"Đã gửi email tới {email_address}")
    return True

st.set_page_config(page_title="Stock Advisor - BinhPT", layout="wide")
st.title("AI Stock Advisor")
st.markdown("#### Tư vấn chứng khoán tự động & cập nhật theo thời gian thực (mỗi 30p)")

email_address = st.text_input("Nhập email để nhận báo cáo tự động (không bắt buộc):", "")

col1, col2 = st.columns(2)
with col1:
    if st.button("Refresh dữ liệu"):
        df = fetch_stock_data()
        st.session_state['df'] = df
        st.session_state['last_update'] = datetime.datetime.now().strftime('%H:%M:%S')
        if email_address:
            send_email(df, email_address)
        st.success(f"Đã cập nhật lúc {st.session_state['last_update']}")
    else:
        if 'df' not in st.session_state:
            st.session_state['df'] = fetch_stock_data()
        df = st.session_state['df']

with col2:
    if 'last_update' in st.session_state:
        st.info(f"Cập nhật lần cuối: {st.session_state['last_update']}")
    else:
        st.info("Chưa có cập nhật mới.")

st.dataframe(df, use_container_width=True)

st.caption("Ứng dụng thử nghiệm, dữ liệu demo (kết nối API/crawler thực khi triển khai chính thức).")
