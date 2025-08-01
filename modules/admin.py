import streamlit as st
import psycopg2
import pandas as pd
import base64

# PostgreSQL connection
def connect_pg():
    return psycopg2.connect(
        dbname="skillsync",
        user="nisha",
        password="12345",  # Replace if needed
        host="localhost",
        port="5432"
    )

# Admin login
def authenticate_admin(username, password):
    return username == "deep" and password == "dp10"

# Get uploaded resumes
def get_uploaded_pdfs():
    try:
        conn = connect_pg()
        cursor = conn.cursor()
        cursor.execute("SELECT id, resume_filename FROM user_profiles WHERE resume_file IS NOT NULL")
        uploaded_pdfs = cursor.fetchall()
        conn.close()
        return uploaded_pdfs
    except Exception as e:
        st.error(f"Error fetching uploaded PDFs: {e}")
        return []

# Fetch resume binary data
def get_pdf_data(pdf_id):
    try:
        conn = connect_pg()
        cursor = conn.cursor()
        cursor.execute("SELECT resume_filename, resume_file FROM user_profiles WHERE id = %s", (pdf_id,))
        pdf_data = cursor.fetchone()
        conn.close()
        return pdf_data
    except Exception as e:
        st.error(f"Error fetching PDF data: {e}")
        return None

# Delete resume
def delete_resume(pdf_id):
    try:
        conn = connect_pg()
        cursor = conn.cursor()
        cursor.execute("UPDATE user_profiles SET resume_file = NULL, resume_filename = NULL WHERE id = %s", (pdf_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error deleting resume: {e}")

# Show uploaded resumes
def display_uploaded_pdfs():
    uploaded_pdfs = get_uploaded_pdfs()
    if uploaded_pdfs:
        st.subheader("Uploaded Resumes")

        for pdf_id, pdf_name in uploaded_pdfs:
            pdf_data = get_pdf_data(pdf_id)
            if pdf_data and pdf_data[1] is not None:
                pdf_b64 = base64.b64encode(pdf_data[1]).decode("utf-8")
                download_link = f'<a href="data:application/pdf;base64,{pdf_b64}" download="{pdf_name}">Download</a>'

                with st.form(key=f"delete_form_{pdf_id}"):
                    st.markdown(f"**{pdf_name}** &nbsp;&nbsp;&nbsp; {download_link}", unsafe_allow_html=True)
                    delete = st.form_submit_button(label="Delete")
                    if delete:
                        delete_resume(pdf_id)
                        st.success(f"Deleted resume: {pdf_name}")
                        st.rerun()
            else:
                st.warning(f"Failed to fetch data for resume ID {pdf_id}")
    else:
        st.info("No uploaded resumes found.")

# Show feedbacks
def display_feedback_data():
    try:
        conn = connect_pg()
        cursor = conn.cursor()
        cursor.execute("SELECT user_name, feedback FROM feedback ORDER BY id DESC LIMIT 10")
        feedbacks = cursor.fetchall()
        conn.close()

        if feedbacks:
            df = pd.DataFrame(feedbacks, columns=["Name", "Feedback"])
            st.subheader("Latest Feedbacks")
            st.dataframe(df)

            if st.button("View All Feedbacks"):
                conn = connect_pg()
                cursor = conn.cursor()
                cursor.execute("SELECT user_name, feedback FROM feedback ORDER BY id DESC")
                all_feedbacks = cursor.fetchall()
                conn.close()
                df_all = pd.DataFrame(all_feedbacks, columns=["Name", "Feedback"])
                st.dataframe(df_all)
        else:
            st.info("No feedback data available.")
    except Exception as e:
        st.error(f"Error loading feedbacks: {e}")

# Admin panel logic
def process_admin_mode():
    st.title("Admin Panel")

    if not st.session_state.get("logged_in"):
        st.subheader("Authentication Required")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate_admin(username, password):
                st.session_state.logged_in = True
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Invalid credentials. Try again.")
        return

    display_uploaded_pdfs()
    st.markdown("---")
    display_feedback_data()

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

if __name__ == "__main__":
    process_admin_mode()
