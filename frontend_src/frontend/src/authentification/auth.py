import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

STREAMLIT_USER_PASSWORD = os.environ.get("STREAMLIT_USER_PASSWORD", None)


def check_password():
    """Returns True if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            "password" in st.session_state
            and st.session_state["password"]
            and st.session_state["password"] in [st.secrets["password_user"], STREAMLIT_USER_PASSWORD]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password

        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True
