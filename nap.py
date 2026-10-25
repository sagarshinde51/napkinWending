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
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Login Form
if not st.session_state.authenticated:
    st.title("Sanitary Napkin Dispensing and Disposing System")
    st.subheader("Admin Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
            if username == "admin" and password == "admin":
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.stop()

# Header & Logout
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.title("Sanitary Napkin Dispensing and Disposing System")
with col_logout:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# Application Tabs
tab1, tab2, tab3 = st.tabs(["📜 Dispense History", "➕ Register New User", "💳 Update Balance"])

# -------------------------------------------------------------
# TAB 1: HISTORY (napkinHistory)
# -------------------------------------------------------------
with tab1:
    st.subheader("Dispense & Disposal History")

    if st.button("🔄 Refresh History"):
        st.rerun()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Matches columns: id, DateTime, Name, RFIDNo, Mobile from napkinHistory[cite: 2]
        cursor.execute("SELECT id, DateTime, Name, RFIDNo, Mobile FROM napkinHistory ORDER BY id DESC")
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

# -------------------------------------------------------------
# TAB 2: CREATE USER (NapkinUsers)
# -------------------------------------------------------------
with tab2:
    st.subheader("Register New User")

    with st.form("create_user_form", clear_on_submit=True):
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            name = st.text_input("Full Name")
            rfid_no = st.text_input("RFID Number")
        with col_u2:
            mobile = st.text_input("Mobile Number")
            email = st.text_input("Email (Optional)")

        balance = st.number_input("Initial Balance", min_value=0, value=100, step=10)
        submit_user = st.form_submit_button("Save User")

        if submit_user:
            if not name.strip() or not rfid_no.strip() or not mobile.strip():
                st.warning("Please fill in all mandatory fields: Name, RFID Number, and Mobile.")
            else:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor(dictionary=True)
                    # Check for duplicate RFID or Mobile in NapkinUsers[cite: 1]
                    cursor.execute(
                        "SELECT id FROM NapkinUsers WHERE RFIDNo = %s OR Mobile = %s",
                        (rfid_no.strip(), mobile.strip())
                    )
                    existing = cursor.fetchone()

                    if existing:
                        st.error("A user with this RFID Number or Mobile already exists!")
                    else:
                        sql = """
                        INSERT INTO NapkinUsers (Name, RFIDNo, Mobile, Email, Balance)
                        VALUES (%s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql, (
                            name.strip(),
                            rfid_no.strip(),
                            mobile.strip(),
                            email.strip() if email else "",
                            str(balance)
                        ))
                        conn.commit()
                        st.success(f"User '{name}' registered successfully with an initial balance of {balance}!")
                    cursor.close()
                    conn.close()
                except mysql.connector.Error as err:
                    st.error(f"Database error: {err}")

# -------------------------------------------------------------
# TAB 3: UPDATE BALANCE (NapkinUsers)
# -------------------------------------------------------------
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
                )
            else:
                cursor.execute(
                    "SELECT id, Name, RFIDNo, Mobile, Balance FROM NapkinUsers WHERE RFIDNo = %s",
                    (search_query.strip(),)
                )
            user = cursor.fetchone()

            if user:
                st.markdown("#### User Details Found")
                col_i1, col_i2, col_i3, col_i4 = st.columns(4)
                col_i1.metric("Name", user["Name"])
                col_i2.metric("RFID", user["RFIDNo"])
                col_i3.metric("Mobile", user["Mobile"])
                col_i4.metric("Current Balance", user["Balance"])

                st.write("---")
                update_mode = st.radio("Balance Action", ["Add to Current Balance", "Set Direct Balance"], horizontal=True)
                amount = st.number_input("Amount", min_value=1, value=50, step=10)

                if st.button("Update Balance"):
                    try:
                        current_bal = int(user["Balance"]) if str(user["Balance"]).isdigit() else 0
                    except ValueError:
                        current_bal = 0

                    new_bal = (current_bal + amount) if update_mode == "Add to Current Balance" else amount

                    cursor.execute(
                        "UPDATE NapkinUsers SET Balance = %s WHERE id = %s",
                        (str(new_bal), user["id"])
                    )
                    conn.commit()
                    st.success(f"Balance updated successfully! New Balance: {new_bal}")
                    cursor.close()
                    conn.close()
                    st.rerun()
            else:
                st.warning("No user found with the provided details.")
                cursor.close()
                conn.close()
        except mysql.connector.Error as err:
            st.error(f"Database error: {err}")
