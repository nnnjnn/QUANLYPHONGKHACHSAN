import streamlit as st
import mysql.connector
from mysql.connector import Error
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
# AIVEN MYSQL CONFIG
# =========================================================

DB_CONFIG = {
    "host": "mysql-3d53e6d-linhlinh102025-4f61.j.aivencloud.com",
    "port": 12534,
    "user": "avnadmin",
    "password": "AVNS_xCvNg6GogirYjn1YxYI",
    "database": "defaultdb",

    # Aiven yêu cầu SSL
    "ssl_disabled": False,
    "ssl_verify_cert": False,
    "ssl_verify_identity": False,

    "autocommit": False
}


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    """
    Tạo kết nối đến MySQL Aiven.
    """

    try:
        conn = mysql.connector.connect(**DB_CONFIG)

        if conn.is_connected():
            return conn

        return None

    except Error as e:
        st.error(f"❌ Không thể kết nối MySQL Aiven: {e}")
        return None


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    conn = get_connection()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        # -------------------------------------------------
        # BẢNG PHÒNG
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_number VARCHAR(20) UNIQUE NOT NULL,
                room_type VARCHAR(50) NOT NULL,
                floor INT NOT NULL,
                price DECIMAL(15,2) NOT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'Trống'
            )
        """)

        # -------------------------------------------------
        # BẢNG KHÁCH HÀNG
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                phone VARCHAR(30),
                email VARCHAR(150),
                id_card VARCHAR(50)
            )
        """)

        # -------------------------------------------------
        # BẢNG ĐẶT PHÒNG
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,

                room_id INT NOT NULL,
                guest_id INT NOT NULL,

                check_in DATE NOT NULL,
                check_out DATE NOT NULL,

                adults INT DEFAULT 1,
                children INT DEFAULT 0,

                status VARCHAR(30) NOT NULL DEFAULT 'Đã đặt',

                total DECIMAL(15,2) DEFAULT 0,

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

        # -------------------------------------------------
        # TẠO DỮ LIỆU PHÒNG MẪU NẾU CHƯA CÓ
        # -------------------------------------------------

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
                VALUES (%s, %s, %s, %s, %s)
            """, sample_rooms)

        conn.commit()

        return True

    except Error as e:

        conn.rollback()

        st.error(
            f"❌ Lỗi khởi tạo database: {e}"
        )

        return False

    finally:

        cursor.close()
        conn.close()


# Khởi tạo database
database_ready = init_database()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def format_currency(value):

    if value is None:
        value = 0

    return f"{float(value):,.0f} VNĐ"


# =========================================================
# GET ROOMS
# =========================================================

def get_rooms():

    conn = get_connection()

    if conn is None:
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
            ORDER BY CAST(room_number AS UNSIGNED)
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as e:

        st.error(
            f"❌ Không thể lấy danh sách phòng: {e}"
        )

        return pd.DataFrame()

    finally:

        conn.close()


# =========================================================
# GET GUESTS
# =========================================================

def get_guests():

    conn = get_connection()

    if conn is None:
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

        return pd.read_sql(query, conn)

    except Exception as e:

        st.error(
            f"❌ Không thể lấy danh sách khách hàng: {e}"
        )

        return pd.DataFrame()

    finally:

        conn.close()


# =========================================================
# GET BOOKINGS
# =========================================================

def get_bookings():

    conn = get_connection()

    if conn is None:
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

            ORDER BY bookings.id DESC
        """

        return pd.read_sql(query, conn)

    except Exception as e:

        st.error(
            f"❌ Không thể lấy danh sách đặt phòng: {e}"
        )

        return pd.DataFrame()

    finally:

        conn.close()


# =========================================================
# UPDATE ROOM STATUS
# =========================================================

def update_room_status(room_id, status):

    conn = get_connection()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE rooms
            SET status = %s
            WHERE id = %s
        """, (
            status,
            room_id
        ))

        conn.commit()

        return True

    except Error as e:

        conn.rollback()

        st.error(
            f"❌ Không thể cập nhật trạng thái phòng: {e}"
        )

        return False

    finally:

        cursor.close()
        conn.close()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🏨 HOTEL MANAGER")

st.sidebar.caption(
    "Hệ thống quản lý phòng khách sạn"
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

st.sidebar.success(
    "🟢 Database: MySQL Aiven"
)

st.sidebar.info(
    "💡 Dữ liệu được lưu trực tiếp trên Aiven MySQL."
)


# =========================================================
# OPTIONAL IMAGE
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

    st.title("📊 Dashboard")

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
            rooms[rooms["status"] == "Trống"]
        )

        occupied = len(
            rooms[rooms["status"] == "Đang ở"]
        )

        reserved = len(
            rooms[rooms["status"] == "Đã đặt"]
        )

        cleaning = len(
            rooms[rooms["status"] == "Đang dọn"]
        )

        occupancy = 0

        if total_rooms > 0:

            occupancy = (
                occupied / total_rooms
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

        # -------------------------------------------------
        # OCCUPANCY
        # -------------------------------------------------

        with col1:

            st.subheader(
                "📌 Công suất phòng"
            )

            st.progress(
                min(occupancy / 100, 1.0)
            )

            st.metric(
                "Công suất hiện tại",
                f"{occupancy:.1f}%"
            )

        # -------------------------------------------------
        # REVENUE
        # -------------------------------------------------

        with col2:

            st.subheader(
                "💰 Doanh thu"
            )

            if not bookings.empty:

                completed = bookings[
                    bookings["status"].isin(
                        [
                            "Đã trả phòng",
                            "Đang ở"
                        ]
                    )
                ]

                revenue = completed[
                    "total"
                ].sum()

            else:

                revenue = 0

            st.metric(
                "Tổng doanh thu",
                format_currency(revenue)
            )

        st.divider()

        # -------------------------------------------------
        # ROOM STATUS
        # -------------------------------------------------

        st.subheader(
            "🛏️ Tình trạng phòng"
        )

        display_rooms = rooms[
            [
                "room_number",
                "room_type",
                "floor",
                "price",
                "status"
            ]
        ].copy()

        display_rooms.columns = [
            "Số phòng",
            "Loại phòng",
            "Tầng",
            "Giá/đêm",
            "Trạng thái"
        ]

        display_rooms[
            "Giá/đêm"
        ] = display_rooms[
            "Giá/đêm"
        ].apply(format_currency)

        st.dataframe(
            display_rooms,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# ROOM MANAGEMENT
# =========================================================

elif menu == "🛏️ Quản lý phòng":

    st.title("🛏️ Quản lý phòng")

    tabs = st.tabs(
        [
            "📋 Danh sách phòng",
            "➕ Thêm phòng",
            "✏️ Cập nhật phòng"
        ]
    )

    # =====================================================
    # ROOM LIST
    # =====================================================

    with tabs[0]:

        rooms = get_rooms()

        if rooms.empty:

            st.info(
                "Chưa có phòng nào."
            )

        else:

            col1, col2 = st.columns(2)

            with col1:

                search = st.text_input(
                    "🔎 Tìm phòng",
                    placeholder="Nhập số phòng..."
                )

            with col2:

                status_filter = st.selectbox(
                    "Lọc trạng thái",
                    [
                        "Tất cả",
                        "Trống",
                        "Đã đặt",
                        "Đang ở",
                        "Đang dọn"
                    ]
                )

            filtered = rooms.copy()

            if search:

                filtered = filtered[
                    filtered[
                        "room_number"
                    ].astype(str).str.contains(
                        search,
                        case=False,
                        na=False
                    )
                ]

            if status_filter != "Tất cả":

                filtered = filtered[
                    filtered["status"]
                    == status_filter
                ]

            display = filtered.rename(
                columns={
                    "room_number": "Số phòng",
                    "room_type": "Loại phòng",
                    "floor": "Tầng",
                    "price": "Giá/đêm",
                    "status": "Trạng thái"
                }
            )

            display = display[
                [
                    "Số phòng",
                    "Loại phòng",
                    "Tầng",
                    "Giá/đêm",
                    "Trạng thái"
                ]
            ]

            display["Giá/đêm"] = display[
                "Giá/đêm"
            ].apply(format_currency)

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

    # =====================================================
    # ADD ROOM
    # =====================================================

    with tabs[1]:

        st.subheader(
            "➕ Thêm phòng mới"
        )

        with st.form("add_room"):

            col1, col2 = st.columns(2)

            with col1:

                room_number = st.text_input(
                    "Số phòng *"
                )

                room_type = st.selectbox(
                    "Loại phòng",
                    [
                        "Standard",
                        "Superior",
                        "Deluxe",
                        "Suite",
                        "Family"
                    ]
                )

            with col2:

                floor = st.number_input(
                    "Tầng",
                    min_value=1,
                    max_value=100,
                    value=1
                )

                price = st.number_input(
                    "Giá phòng/đêm",
                    min_value=0,
                    value=700000,
                    step=50000
                )

            submitted = st.form_submit_button(
                "➕ Thêm phòng",
                use_container_width=True
            )

        if submitted:

            if not room_number.strip():

                st.error(
                    "Vui lòng nhập số phòng."
                )

            else:

                conn = get_connection()

                if conn:

                    cursor = conn.cursor()

                    try:

                        cursor.execute("""
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
                        """, (
                            room_number.strip(),
                            room_type,
                            floor,
                            price,
                            "Trống"
                        ))

                        conn.commit()

                        st.success(
                            f"Đã thêm phòng {room_number}!"
                        )

                        st.rerun()

                    except Error as e:

                        conn.rollback()

                        if e.errno == 1062:

                            st.error(
                                "Số phòng này đã tồn tại."
                            )

                        else:

                            st.error(
                                f"❌ Lỗi: {e}"
                            )

                    finally:

                        cursor.close()
                        conn.close()

    # =====================================================
    # UPDATE ROOM
    # =====================================================

    with tabs[2]:

        rooms = get_rooms()

        if rooms.empty:

            st.warning(
                "Chưa có phòng."
            )

        else:

            room_options = (
                rooms["room_number"]
                .tolist()
            )

            selected_room = st.selectbox(
                "Chọn phòng",
                room_options
            )

            room = rooms[
                rooms["room_number"]
                == selected_room
            ].iloc[0]

            room_types = [
                "Standard",
                "Superior",
                "Deluxe",
                "Suite",
                "Family"
            ]

            statuses = [
                "Trống",
                "Đã đặt",
                "Đang ở",
                "Đang dọn"
            ]

            with st.form(
                "update_room"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    new_type = st.selectbox(
                        "Loại phòng",
                        room_types,
                        index=room_types.index(
                            room["room_type"]
                        )
                    )

                    new_floor = st.number_input(
                        "Tầng",
                        min_value=1,
                        value=int(
                            room["floor"]
                        )
                    )

                with col2:

                    new_price = st.number_input(
                        "Giá/đêm",
                        min_value=0,
                        value=int(
                            room["price"]
                        ),
                        step=50000
                    )

                    new_status = st.selectbox(
                        "Trạng thái",
                        statuses,
                        index=statuses.index(
                            room["status"]
                        )
                    )

                update = st.form_submit_button(
                    "💾 Lưu thay đổi",
                    use_container_width=True
                )

            if update:

                conn = get_connection()

                if conn:

                    cursor = conn.cursor()

                    try:

                        cursor.execute("""
                            UPDATE rooms
                            SET
                                room_type = %s,
                                floor = %s,
                                price = %s,
                                status = %s
                            WHERE room_number = %s
                        """, (
                            new_type,
                            new_floor,
                            new_price,
                            new_status,
                            selected_room
                        ))

                        conn.commit()

                        st.success(
                            "Đã cập nhật thông tin phòng."
                        )

                        st.rerun()

                    except Error as e:

                        conn.rollback()

                        st.error(
                            f"❌ Lỗi: {e}"
                        )

                    finally:

                        cursor.close()
                        conn.close()


# =========================================================
# BOOKING
# =========================================================

elif menu == "📅 Đặt phòng":

    st.title("📅 Đặt phòng")

    rooms = get_rooms()

    available_rooms = rooms[
        rooms["status"] == "Trống"
    ]

    if available_rooms.empty:

        st.warning(
            "Hiện tại không có phòng trống."
        )

    else:

        st.subheader(
            "Thông tin đặt phòng"
        )

        with st.form(
            "booking_form"
        ):

            col1, col2 = st.columns(2)

            with col1:

                guest_name = st.text_input(
                    "Tên khách *"
                )

                phone = st.text_input(
                    "Số điện thoại"
                )

                email = st.text_input(
                    "Email"
                )

                id_card = st.text_input(
                    "CCCD / Passport"
                )

            with col2:

                room_number = st.selectbox(
                    "Chọn phòng",
                    available_rooms[
                        "room_number"
                    ].tolist()
                )

                check_in = st.date_input(
                    "Ngày nhận phòng",
                    value=date.today()
                )

                check_out = st.date_input(
                    "Ngày trả phòng",
                    value=date.today()
                )

                adults = st.number_input(
                    "Số người lớn",
                    min_value=1,
                    value=1
                )

                children = st.number_input(
                    "Số trẻ em",
                    min_value=0,
                    value=0
                )

            create_booking = st.form_submit_button(
                "📅 Xác nhận đặt phòng",
                use_container_width=True
            )

        if create_booking:

            if not guest_name.strip():

                st.error(
                    "Vui lòng nhập tên khách."
                )

            elif check_out <= check_in:

                st.error(
                    "Ngày trả phòng phải sau ngày nhận phòng."
                )

            else:

                selected = available_rooms[
                    available_rooms[
                        "room_number"
                    ] == room_number
                ].iloc[0]

                nights = (
                    check_out - check_in
                ).days

                total = (
                    nights
                    * float(selected["price"])
                )

                conn = get_connection()

                if conn:

                    cursor = conn.cursor()

                    try:

                        # ---------------------------------
                        # THÊM KHÁCH
                        # ---------------------------------

                        cursor.execute("""
                            INSERT INTO guests
                            (
                                name,
                                phone,
                                email,
                                id_card
                            )
                            VALUES
                            (%s, %s, %s, %s)
                        """, (
                            guest_name.strip(),
                            phone,
                            email,
                            id_card
                        ))

                        guest_id = cursor.lastrowid

                        # ---------------------------------
                        # THÊM BOOKING
                        # ---------------------------------

                        cursor.execute("""
                            INSERT INTO bookings
                            (
                                room_id,
                                guest_id,
                                check_in,
                                check_out,
                                adults,
                                children,
                                status,
                                total,
                                created_at
                            )
                            VALUES
                            (
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s
                            )
                        """, (
                            int(selected["id"]),
                            guest_id,
                            check_in,
                            check_out,
                            adults,
                            children,
                            "Đã đặt",
                            total,
                            datetime.now()
                        ))

                        # ---------------------------------
                        # ĐỔI TRẠNG THÁI PHÒNG
                        # ---------------------------------

                        cursor.execute("""
                            UPDATE rooms
                            SET status = 'Đã đặt'
                            WHERE id = %s
                        """, (
                            int(selected["id"]),
                        ))

                        conn.commit()

                        st.success(
                            f"Đặt phòng {room_number} thành công!"
                        )

                        st.info(
                            f"Tổng tiền: "
                            f"{format_currency(total)} "
                            f"({nights} đêm)"
                        )

                    except Error as e:

                        conn.rollback()

                        st.error(
                            f"❌ Không thể tạo đặt phòng: {e}"
                        )

                    finally:

                        cursor.close()
                        conn.close()


# =========================================================
# GUEST MANAGEMENT
# =========================================================

elif menu == "👤 Khách hàng":

    st.title(
        "👤 Quản lý khách hàng"
    )

    guests = get_guests()

    if guests.empty:

        st.info(
            "Chưa có khách hàng nào."
        )

    else:

        st.subheader(
            "🔎 Danh sách khách hàng"
        )

        search_guest = st.text_input(
            "Tìm theo tên / số điện thoại"
        )

        filtered = guests.copy()

        if search_guest:

            name_mask = (
                filtered["name"]
                .astype(str)
                .str.contains(
                    search_guest,
                    case=False,
                    na=False
                )
            )

            phone_mask = (
                filtered["phone"]
                .fillna("")
                .astype(str)
                .str.contains(
                    search_guest,
                    case=False,
                    na=False
                )
            )

            filtered = filtered[
                name_mask | phone_mask
            ]

        display_guests = filtered.rename(
            columns={
                "name": "Họ tên",
                "phone": "Số điện thoại",
                "email": "Email",
                "id_card": "CCCD / Passport"
            }
        )

        display_guests = display_guests[
            [
                "Họ tên",
                "Số điện thoại",
                "Email",
                "CCCD / Passport"
            ]
        ]

        st.dataframe(
            display_guests,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# CURRENT BOOKINGS
# =========================================================

elif menu == "💰 Đặt phòng hiện tại":

    st.title(
        "💰 Quản lý đặt phòng"
    )

    bookings = get_bookings()

    if bookings.empty:

        st.info(
            "Chưa có đặt phòng nào."
        )

    else:

        for _, booking in bookings.iterrows():

            with st.container(
                border=True
            ):

                col1, col2, col3, col4 = st.columns(
                    [1, 2, 2, 1]
                )

                # -----------------------------------------
                # ROOM
                # -----------------------------------------

                with col1:

                    st.subheader(
                        f"Phòng "
                        f"{booking['room_number']}"
                    )

                    st.caption(
                        booking["room_type"]
                    )

                # -----------------------------------------
                # GUEST
                # -----------------------------------------

                with col2:

                    st.write(
                        f"👤 **{booking['guest_name']}**"
                    )

                    st.write(
                        f"📞 "
                        f"{booking['phone'] or 'Chưa có'}"
                    )

                # -----------------------------------------
                # BOOKING
                # -----------------------------------------

                with col3:

                    st.write(
                        f"📅 "
                        f"{booking['check_in']} → "
                        f"{booking['check_out']}"
                    )

                    st.write(
                        f"💰 "
                        f"{format_currency(booking['total'])}"
                    )

                # -----------------------------------------
                # ACTION
                # -----------------------------------------

                with col4:

                    status = booking["status"]

                    if status == "Đã đặt":

                        if st.button(
                            "🏨 Check-in",
                            key=f"checkin_{booking['id']}"
                        ):

                            conn = get_connection()

                            if conn:

                                cursor = conn.cursor()

                                try:

                                    cursor.execute("""
                                        UPDATE bookings
                                        SET status = 'Đang ở'
                                        WHERE id = %s
                                    """, (
                                        int(
                                            booking["id"]
                                        ),
                                    ))

                                    cursor.execute("""
                                        UPDATE rooms
                                        SET status = 'Đang ở'
                                        WHERE room_number = %s
                                    """, (
                                        booking[
                                            "room_number"
                                        ],
                                    ))

                                    conn.commit()

                                    st.success(
                                        "Đã check-in."
                                    )

                                    st.rerun()

                                except Error as e:

                                    conn.rollback()

                                    st.error(
                                        f"❌ Lỗi: {e}"
                                    )

                                finally:

                                    cursor.close()
                                    conn.close()

                    elif status == "Đang ở":

                        if st.button(
                            "🚪 Check-out",
                            key=f"checkout_{booking['id']}"
                        ):

                            conn = get_connection()

                            if conn:

                                cursor = conn.cursor()

                                try:

                                    cursor.execute("""
                                        UPDATE bookings
                                        SET status = 'Đã trả phòng'
                                        WHERE id = %s
                                    """, (
                                        int(
                                            booking["id"]
                                        ),
                                    ))

                                    cursor.execute("""
                                        UPDATE rooms
                                        SET status = 'Đang dọn'
                                        WHERE room_number = %s
                                    """, (
                                        booking[
                                            "room_number"
                                        ],
                                    ))

                                    conn.commit()

                                    st.success(
                                        "Đã check-out khách."
                                    )

                                    st.rerun()

                                except Error as e:

                                    conn.rollback()

                                    st.error(
                                        f"❌ Lỗi: {e}"
                                    )

                                finally:

                                    cursor.close()
                                    conn.close()

                    elif status == "Đã trả phòng":

                        st.success(
                            "Đã trả phòng"
                        )

                    else:

                        st.warning(
                            status
                        )


# =========================================================
# REPORT
# =========================================================

elif menu == "📈 Báo cáo":

    st.title(
        "📈 Báo cáo & thống kê"
    )

    rooms = get_rooms()
    bookings = get_bookings()

    # =====================================================
    # ROOM STATUS
    # =====================================================

    st.subheader(
        "🛏️ Thống kê trạng thái phòng"
    )

    if not rooms.empty:

        status_count = (
            rooms["status"]
            .value_counts()
            .reset_index()
        )

        status_count.columns = [
            "Trạng thái",
            "Số lượng"
        ]

        st.bar_chart(
            status_count.set_index(
                "Trạng thái"
            )
        )

    else:

        st.info(
            "Chưa có dữ liệu phòng."
        )

    # =====================================================
    # REVENUE
    # =====================================================

    st.subheader(
        "💰 Doanh thu"
    )

    if bookings.empty:

        st.info(
            "Chưa có dữ liệu doanh thu."
        )

    else:

        completed_bookings = bookings[
            bookings["status"].isin(
                [
                    "Đang ở",
                    "Đã trả phòng"
                ]
            )
        ]

        revenue = (
            completed_bookings["total"]
            .sum()
        )

        st.metric(
            "Tổng doanh thu",
            format_currency(revenue)
        )

        revenue_by_room = (
            completed_bookings
            .groupby("room_number")["total"]
            .sum()
            .reset_index()
        )

        revenue_by_room.columns = [
            "Số phòng",
            "Doanh thu"
        ]

        if not revenue_by_room.empty:

            st.bar_chart(
                revenue_by_room.set_index(
                    "Số phòng"
                )
            )

    # =====================================================
    # EXPORT
    # =====================================================

    st.subheader(
        "📥 Xuất dữ liệu"
    )

    if not bookings.empty:

        csv_bookings = (
            bookings
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(
            label="📥 Tải danh sách đặt phòng CSV",
            data=csv_bookings,
            file_name="bookings.csv",
            mime="text/csv"
        )

    if not rooms.empty:

        csv_rooms = (
            rooms
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(
            label="📥 Tải danh sách phòng CSV",
            data=csv_rooms,
            file_name="rooms.csv",
            mime="text/csv"
        )

    if not guests.empty:

        csv_guests = (
            guests
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(
            label="📥 Tải danh sách khách hàng CSV",
            data=csv_guests,
            file_name="guests.csv",
            mime="text/csv"
        )
