import streamlit as st
import mysql.connector
from datetime import datetime, date
import pandas as pd
import os


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Hotel Room Manager",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# AIVEN MYSQL DATABASE
# =========================================================

DB_CONFIG = {
    "host": "mysql-3d53e6d-linhlinh102025-4f61.j.aivencloud.com",
    "port": 12534,
    "user": "avnadmin",
    "password": "AVNS_xCvNg6GogirYjn1YxYI",
    "database": "defaultdb",

    # SSL của Aiven
    "ssl_disabled": False,
    "ssl_verify_cert": False,
    "ssl_verify_identity": False
}


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    try:

        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            ssl_disabled=DB_CONFIG["ssl_disabled"],
            ssl_verify_cert=DB_CONFIG["ssl_verify_cert"],
            ssl_verify_identity=DB_CONFIG["ssl_verify_identity"]
        )

        if connection.is_connected():
            return connection

        return None

    except mysql.connector.Error as e:

        st.error(
            f"❌ Không kết nối được MySQL Aiven: {e}"
        )

        return None


# =========================================================
# TEST DATABASE
# =========================================================

def test_database():

    connection = get_connection()

    if connection is None:
        return False

    try:

        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE()")

        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            return True

        return False

    except mysql.connector.Error as e:

        st.error(
            f"❌ Lỗi kiểm tra database: {e}"
        )

        return False


# =========================================================
# CREATE TABLES
# =========================================================

def init_database():

    connection = get_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:

        # =====================================================
        # ROOMS
        # =====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (

                id INT AUTO_INCREMENT PRIMARY KEY,

                room_number VARCHAR(20)
                    NOT NULL UNIQUE,

                room_type VARCHAR(50)
                    NOT NULL,

                floor INT
                    NOT NULL,

                price DECIMAL(15,2)
                    NOT NULL,

                status VARCHAR(30)
                    NOT NULL DEFAULT 'Trống'

            )
        """)

        # =====================================================
        # GUESTS
        # =====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guests (

                id INT AUTO_INCREMENT PRIMARY KEY,

                name VARCHAR(150)
                    NOT NULL,

                phone VARCHAR(30),

                email VARCHAR(150),

                id_card VARCHAR(50)

            )
        """)

        # =====================================================
        # BOOKINGS
        # =====================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (

                id INT AUTO_INCREMENT PRIMARY KEY,

                room_id INT NOT NULL,

                guest_id INT NOT NULL,

                check_in DATE NOT NULL,

                check_out DATE NOT NULL,

                adults INT DEFAULT 1,

                children INT DEFAULT 0,

                status VARCHAR(30)
                    NOT NULL DEFAULT 'Đã đặt',

                total DECIMAL(15,2)
                    DEFAULT 0,

                created_at DATETIME NOT NULL,

                FOREIGN KEY (room_id)
                    REFERENCES rooms(id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,

                FOREIGN KEY (guest_id)
                    REFERENCES guests(id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE

            )
        """)

        # =====================================================
        # INSERT SAMPLE ROOMS
        # =====================================================

        cursor.execute(
            "SELECT COUNT(*) FROM rooms"
        )

        room_count = cursor.fetchone()[0]

        if room_count == 0:

            sample_rooms = [

                ("101", "Standard", 1, 700000, "Trống"),
                ("102", "Standard", 1, 700000, "Trống"),
                ("103", "Standard", 1, 700000, "Trống"),

                ("201", "Superior", 2, 1000000, "Trống"),
                ("202", "Superior", 2, 1000000, "Trống"),
                ("203", "Superior", 2, 1000000, "Trống"),

                ("301", "Deluxe", 3, 1400000, "Trống"),
                ("302", "Deluxe", 3, 1400000, "Trống"),

                ("401", "Suite", 4, 2200000, "Trống"),
                ("402", "Suite", 4, 2200000, "Trống")

            ]

            cursor.executemany("""
                INSERT INTO rooms
                (
                    room_number,
                    room_type,
                    floor,
                    price,
                    status
                )
                VALUES
                (%s, %s, %s, %s, %s)
            """, sample_rooms)

        connection.commit()

        cursor.close()
        connection.close()

        return True

    except mysql.connector.Error as e:

        connection.rollback()

        st.error(
            f"❌ Lỗi tạo database: {e}"
        )

        cursor.close()
        connection.close()

        return False


# =========================================================
# START DATABASE
# =========================================================

database_ready = init_database()


# =========================================================
# FORMAT MONEY
# =========================================================

def format_currency(value):

    if value is None:
        value = 0

    return f"{float(value):,.0f} VNĐ"


# =========================================================
# GET ROOMS
# =========================================================

def get_rooms():

    connection = get_connection()

    if connection is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                room_number,
                room_type,
                floor,
                price,
                status

            FROM rooms

            ORDER BY
                CAST(room_number AS UNSIGNED)
        """

        df = pd.read_sql(
            query,
            connection
        )

        connection.close()

        return df

    except Exception as e:

        st.error(
            f"❌ Lỗi lấy phòng: {e}"
        )

        connection.close()

        return pd.DataFrame()


# =========================================================
# GET GUESTS
# =========================================================

def get_guests():

    connection = get_connection()

    if connection is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                name,
                phone,
                email,
                id_card

            FROM guests

            ORDER BY id DESC
        """

        df = pd.read_sql(
            query,
            connection
        )

        connection.close()

        return df

    except Exception as e:

        st.error(
            f"❌ Lỗi lấy khách hàng: {e}"
        )

        connection.close()

        return pd.DataFrame()


# =========================================================
# GET BOOKINGS
# =========================================================

def get_bookings():

    connection = get_connection()

    if connection is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT

                bookings.id,

                rooms.room_number,

                rooms.room_type,

                guests.name AS guest_name,

                guests.phone,

                guests.email,

                guests.id_card,

                bookings.check_in,

                bookings.check_out,

                bookings.adults,

                bookings.children,

                bookings.status,

                bookings.total,

                bookings.created_at

            FROM bookings

            INNER JOIN rooms
                ON bookings.room_id = rooms.id

            INNER JOIN guests
                ON bookings.guest_id = guests.id

            ORDER BY
                bookings.id DESC
        """

        df = pd.read_sql(
            query,
            connection
        )

        connection.close()

        return df

    except Exception as e:

        st.error(
            f"❌ Lỗi lấy đặt phòng: {e}"
        )

        connection.close()

        return pd.DataFrame()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "🏨 HOTEL MANAGER"
)

st.sidebar.caption(
    "Hệ thống quản lý khách sạn"
)

menu = st.sidebar.radio(
    "MENU",
    [
        "📊 Dashboard",
        "🛏️ Quản lý phòng",
        "📅 Đặt phòng",
        "👤 Khách hàng",
        "💰 Đặt phòng hiện tại",
        "📈 Báo cáo"
    ]
)

st.sidebar.divider()

if database_ready:

    st.sidebar.success(
        "🟢 MySQL Aiven: Đã kết nối"
    )

else:

    st.sidebar.error(
        "🔴 MySQL Aiven: Lỗi kết nối"
    )


# =========================================================
# IMAGE
# =========================================================

if os.path.exists("images.jpg"):

    st.image(
        "images.jpg",
        use_container_width=True
    )


# =========================================================
# DASHBOARD
# =========================================================

if menu == "📊 Dashboard":

    st.title(
        "📊 Dashboard"
    )

    st.write(
        "Tổng quan tình trạng khách sạn"
    )

    rooms = get_rooms()
    bookings = get_bookings()

    if rooms.empty:

        st.warning(
            "Chưa có dữ liệu phòng."
        )

    else:

        total_rooms = len(rooms)

        available = len(
            rooms[
                rooms["status"] == "Trống"
            ]
        )

        occupied = len(
            rooms[
                rooms["status"] == "Đang ở"
            ]
        )

        reserved = len(
            rooms[
                rooms["status"] == "Đã đặt"
            ]
        )

        cleaning = len(
            rooms[
                rooms["status"] == "Đang dọn"
            ]
        )

        occupancy = 0

        if total_rooms > 0:

            occupancy = (
                occupied /
                total_rooms
            ) * 100

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "🏨 Tổng phòng",
            total_rooms
        )

        col2.metric(
            "🟢 Phòng trống",
            available
        )

        col3.metric(
            "🔴 Đang ở",
            occupied
        )

        col4.metric(
            "🟡 Đã đặt",
            reserved
        )

        col5.metric(
            "🧹 Đang dọn",
            cleaning
        )

        st.divider()

        col1, col2 = st.columns(2)

        with col1:

            st.subheader(
                "📌 Công suất phòng"
            )

            st.progress(
                min(
                    occupancy / 100,
                    1.0
                )
            )

            st.metric(
                "Công suất hiện tại",
                f"{occupancy:.1f}%"
            )

        with col2:

            st.subheader(
               
