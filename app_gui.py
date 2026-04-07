# ONLY showing the changed section to keep this clean 👇
# Replace your EXISTING st.markdown("<style>...") block with THIS

st.markdown(
    """
    <style>
    /* ==============================
       GLOBAL INPUT + DROPDOWN FIX
       ============================== */

    /* Closed select */
    div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }

    div[data-baseweb="select"] input {
        -webkit-text-fill-color: #ffffff !important;
    }

    /* Dropdown container */
    div[data-baseweb="popover"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }

    div[data-baseweb="popover"] * {
        color: #ffffff !important;
    }

    /* Menu */
    div[data-baseweb="menu"] {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="menu"] * {
        color: #ffffff !important;
    }

    /* Options */
    ul[role="listbox"],
    div[role="listbox"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }

    li[role="option"],
    div[role="option"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }

    li[role="option"]:hover,
    li[role="option"][aria-selected="true"],
    div[role="option"]:hover {
        background-color: #14532d !important;
        color: #ffffff !important;
    }

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        background: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #cbd5e1 !important;
    }

    /* Buttons */
    .stButton > button {
        background: #14532d !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }

    .stButton > button:hover {
        background: #166534 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)