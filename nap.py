import streamlit as st
import mysql.connector
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Sanitary Napkin Dispensing & Disposing System",
    page_icon="🌸",
    layout="wide"
)

# Database Connection Helper using mysql.connector
def get_db_connection():
    return mysql.connector.connect(
        host="82.180.143.66",
        user="u263681140_students",
        password="testStudents@123",
        database="u263681140_students"
    )

# Session State for Authentication
if "role" not in st.session_state:
    st.session_state.role = None  # 'admin' or 'user'
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# -------------------------------------------------------------
# LOGIN SECTION (ADMIN OR USER)
# -------------------------------------------------------------
if st.session_state.role is None:
    st.title("Sanitary Napkin Dispensing and Disposing System")
    st.subheader("Login Portal")

    login_type = st.radio("Select Login Type", ["User Login", "Admin Login"], horizontal=True)

    with st.form("login_form"):
        if login_type == "Admin Login":
            admin_user = st.text_input("Admin Username")
            admin_pass = st.text_input("Admin Password", type="password")
            btn_login = st.form_submit_button("Login as Admin")

            if btn_login:
                if admin_user == "admin" and admin_pass == "admin":
                    st.session_state.role = "admin"
                    st.success("Admin login successful!")
                    st.rerun()
                else:
                    st.error("Invalid admin credentials.")

        else:
            identifier = st.text_input("RFID Number or Mobile Number")
            user_pass = st.text_input("Password", type="password")
            btn_login = st.form_submit_button("Login as User")

            if btn_login:
                if not identifier.strip() or not user_pass.strip():
                    st.warning("Please enter your RFID/Mobile and Password.")
                else:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor(dictionary=True)
                        query = """
                            SELECT id, Name, RFIDNo, Mobile, Email, Balance, password 
                            FROM NapkinUsers 
                            WHERE (RFIDNo = %s OR Mobile = %s) AND password = %s
                            LIMIT 1
                        """
                        cursor.execute(query, (identifier.strip(), identifier.strip(), user_pass.strip()))
                        matched_user = cursor.fetchone()
                        cursor.close()
                        conn.close()

                        if matched_user:
                            st.session_state.role = "user"
                            st.session_state.user_data = matched_user
                            st.success(f"Welcome, {matched_user['Name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid RFID/Mobile number or password.")
                    except mysql.connector.Error as err:
                        st.error(f"Database error: {err}")

    st.stop()

# -------------------------------------------------------------
# HEADER & LOGOUT
# -------------------------------------------------------------
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.title("Sanitary Napkin Dispensing and Disposing System")
with col_logout:
    if st.button("Logout"):
        st.session_state.role = None
        st.session_state.user_data = None
        st.rerun()

# -------------------------------------------------------------
# USER DASHBOARD (IF LOGGED IN AS A USER)
# -------------------------------------------------------------
if st.session_state.role == "user":
    u = st.session_state.user_data
    st.subheader(f"👋 Welcome, {u['Name']}")
    
    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
    col_u1.metric("Name", u["Name"])
    col_u2.metric("RFID Number", u["RFIDNo"])
    col_u3.metric("Mobile", u["Mobile"])
    col_u4.metric("Current Balance", f"₹ {u['Balance']}")

    st.write("---")
    st.subheader("Your Dispense & Disposal History")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT DateTime, Name, RFIDNo, Mobile FROM napkinHistory WHERE RFIDNo = %s OR Mobile = %s ORDER BY id DESC",
            (u["RFIDNo"], u["Mobile"])
        )
        my_history = cursor.fetchall()
        cursor.close()
        conn.close()

        if my_history:
            st.dataframe(pd.DataFrame(my_history), use_container_width=True)
        else:
            st.info("No usage history found for your account.")
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")

# -------------------------------------------------------------
# ADMIN DASHBOARD (IF LOGGED IN AS ADMIN)
# -------------------------------------------------------------
elif st.session_state.role == "admin":
    tab1, tab2, tab3 = st.tabs(["📜 Dispense History", "➕ Register New User", "💳 Update Balance"])

    # ---------------------------------------------------------
    # TAB 1: HISTORY (napkinHistory)
    # ---------------------------------------------------------
    with tab1:
        st.subheader("All Dispense & Disposal History")

        if st.button("🔄 Refresh History"):
            st.rerun()

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, DateTime, Name, RFIDNo, Mobile FROM napkinHistory ORDER BY id DESC")[cite: 2]
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)
                st.caption(f"Total entries: {len(df)}")
            else:
                st.info("No history records found in `napkinHistory`.")
        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")

    # ---------------------------------------------------------
    # TAB 2: CREATE USER (NapkinUsers) with password field
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Register New User")

        with st.form("create_user_form", clear_on_submit=True):
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                name = st.text_input("Full Name")[cite: 3]
                rfid_no = st.text_input("RFID Number")[cite: 3]
                password = st.text_input("Account Password", type="password")[cite: 3]
            with col_u2:
                mobile = st.text_input("Mobile Number")[cite: 3]
                email = st.text_input("Email (Optional)")[cite: 3]
                balance = st.number_input("Initial Balance", min_value=0, value=100, step=10)[cite: 3]

            submit_user = st.form_submit_button("Save User")

            if submit_user:
                if not name.strip() or not rfid_no.strip() or not mobile.strip() or not password.strip():
                    st.warning("Please fill in all mandatory fields: Name, RFID Number, Mobile, and Password.")
                else:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute(
                            "SELECT id FROM NapkinUsers WHERE RFIDNo = %s OR Mobile = %s",
                            (rfid_no.strip(), mobile.strip())
                        )
                        existing = cursor.fetchone()

                        if existing:
                            st.error("A user with this RFID Number or Mobile already exists!")
                        else:
                            # Insert including password into NapkinUsers table
                            sql = """
                            INSERT INTO NapkinUsers (Name, RFIDNo, Mobile, Email, Balance, password)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """[cite: 3]
                            cursor.execute(sql, (
                                name.strip(),
                                rfid_no.strip(),
                                mobile.strip(),
                                email.strip() if email else "",
                                str(balance),
                                password.strip()
                            ))
                            conn.commit()
                            st.success(f"User '{name}' registered successfully! They can now log in using their RFID/Mobile and Password.")
                        cursor.close()
                        conn.close()
                    except mysql.connector.Error as err:
                        st.error(f"Database error: {err}")

    # ---------------------------------------------------------
    # TAB 3: UPDATE BALANCE (NapkinUsers)
    # ---------------------------------------------------------
    with tab3:
        st.subheader("Update User Balance")

        search_type = st.radio("Search By", ["Mobile Number", "RFID Number"], horizontal=True)
        search_query = st.text_input(f"Enter {search_type}")

        if search_query.strip():
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)

                if search_type == "Mobile Number":
                    cursor.execute(
                        "SELECT id, Name, RFIDNo, Mobile, Balance FROM NapkinUsers WHERE Mobile = %s",
                        (search_query.strip(),)
                    )[cite: 3]
                else:
                    cursor.execute(
                        "SELECT id, Name, RFIDNo, Mobile, Balance FROM NapkinUsers WHERE RFIDNo = %s",
                        (search_query.strip(),)
                    )[cite: 3]
                user = cursor.fetchone()

                if user:
                    st.markdown("#### User Details Found")
                    col_i1, col_
