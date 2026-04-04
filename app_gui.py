import streamlit as st

st.set_page_config(page_title="TerravaultIQ", layout="wide")

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
/* Main select field (closed state) */
div[data-baseweb="select"] > div {
    background-color: #1f4d3a !important;
    color: #ffffff !important;
    border: 1px solid #2d6a4f !important;
    border-radius: 8px !important;
}

/* Text inside closed select */
div[data-baseweb="select"] span {
    color: #ffffff !important;
}

/* Placeholder / single value text */
div[data-baseweb="select"] div {
    color: #ffffff !important;
}

/* Dropdown popover background */
div[data-baseweb="popover"] {
    background-color: #1e1e1e !important;
    color: #ffffff !important;
}

/* Dropdown list container */
ul[role="listbox"] {
    background-color: #1e1e1e !important;
    border: 1px solid #2d6a4f !important;
    border-radius: 8px !important;
    padding: 4px !important;
}

/* Individual dropdown options */
li[role="option"] {
    background-color: #1e1e1e !important;
    color: #ffffff !important;
    font-weight: 500 !important;
}

/* Hovered option */
li[role="option"]:hover {
    background-color: #2d6a4f !important;
    color: #ffffff !important;
}

/* Selected / highlighted option */
li[aria-selected="true"] {
    background-color: #40916c !important;
    color: #ffffff !important;
}

/* Inputs */
.stTextInput input, .stTextArea textarea {
    background-color: #163828 !important;
    color: #ffffff !important;
    border: 1px solid #2d6a4f !important;
    border-radius: 8px !important;
}

/* Form container */
div[data-testid="stForm"] {
    background-color: #0f241b;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #2d6a4f;
}

/* Buttons */
.stButton button, .stFormSubmitButton button {
    background-color: #2d6a4f !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
}

.stButton button:hover, .stFormSubmitButton button:hover {
    background-color: #40916c !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- PAGE HEADER ----------
st.title("TerravaultIQ")
st.subheader("Easy Ad Pack Recommendation Form")

st.write(
    "Use this form to help choose the best advertising solution for the customer. "
    "The goal is to make recommendations simple, clear, and easy to explain."
)

# ---------- HELPER DATA ----------
ad_pack_help = {
    "SEO": {
        "why": "Best for customers who want long-term visibility in Google search results and steady organic traffic.",
        "best_for": "Businesses that want to rank higher over time and build trust online.",
        "sales_line": "SEO helps the customer get found more often when people search for what they offer."
    },
    "Google Ads": {
        "why": "Best for customers who want faster leads, calls, and immediate visibility in search.",
        "best_for": "Businesses that want results sooner and need high-intent traffic now.",
        "sales_line": "Google Ads puts the business in front of people already searching for their service."
    },
    "OTT": {
        "why": "Best for customers who want brand awareness through streaming TV targeting.",
        "best_for": "Businesses that want to stay top of mind and reach households in a premium way.",
        "sales_line": "OTT helps the customer build awareness on streaming TV so more people know and remember the brand."
    },
    "Social Media Ads": {
        "why": "Best for customers who want attention, engagement, and reach on platforms people use every day.",
        "best_for": "Businesses trying to generate awareness, clicks, and audience interest.",
        "sales_line": "Social ads help the customer get in front of the right people where they already spend time."
    },
    "Retargeting": {
        "why": "Best for customers who already get traffic but need more conversions.",
        "best_for": "Businesses that want to bring visitors back and stay visible after the first visit.",
        "sales_line": "Retargeting helps turn missed opportunities into conversions by bringing visitors back."
    },
    "Local SEO + Google Ads": {
        "why": "Best for customers who want both quick wins now and stronger long-term search visibility.",
        "best_for": "Local businesses that need leads now but also want to grow their search presence over time.",
        "sales_line": "This gives the customer both immediate traffic and a stronger long-term position online."
    },
    "Full Funnel Package": {
        "why": "Best for customers who need awareness, consideration, and conversion support together.",
        "best_for": "Businesses that want a complete strategy across multiple channels.",
        "sales_line": "This helps the customer attract attention, build trust, and drive action across the whole buyer journey."
    }
}

goal_to_pack = {
    "More website traffic": "SEO",
    "More phone calls fast": "Google Ads",
    "More local leads": "Local SEO + Google Ads",
    "Brand awareness": "OTT",
    "Stay visible to past visitors": "Retargeting",
    "More social engagement": "Social Media Ads",
    "Need a complete strategy": "Full Funnel Package"
}

# ---------- FORM ----------
with st.form("terravaultiq_sales_form"):
    st.markdown("### Customer Information")

    customer_name = st.text_input("Customer name")
    business_name = st.text_input("Business name")
    business_type = st.text_input("Business type")
    customer_goal = st.selectbox(
        "What does the customer want most?",
        list(goal_to_pack.keys())
    )

    # Auto-suggest a package based on goal
    suggested_pack = goal_to_pack[customer_goal]

    st.markdown("### Recommended Ad Pack")

    ad_pack = st.selectbox(
        "What ad pack should you offer?",
        list(ad_pack_help.keys()),
        index=list(ad_pack_help.keys()).index(suggested_pack),
        help="Choose the advertising solution that best matches the customer's goals."
    )

    st.info(f"Suggested based on customer goal: **{suggested_pack}**")

    st.markdown("### Why this helps the customer")
    st.write(f"**Why it works:** {ad_pack_help[ad_pack]['why']}")
    st.write(f"**Best for:** {ad_pack_help[ad_pack]['best_for']}")
    st.write(f"**Simple sales talk track:** {ad_pack_help[ad_pack]['sales_line']}")

    notes = st.text_area(
        "Extra notes about the customer",
        placeholder="Example: Wants more calls, has weak Google presence, needs better awareness locally..."
    )

    submitted = st.form_submit_button("Generate Recommendation")

# ---------- OUTPUT ----------
if submitted:
    st.markdown("## Recommendation Summary")
    st.write(f"**Customer name:** {customer_name or 'Not provided'}")
    st.write(f"**Business name:** {business_name or 'Not provided'}")
    st.write(f"**Business type:** {business_type or 'Not provided'}")
    st.write(f"**Primary goal:** {customer_goal}")
    st.write(f"**Recommended ad pack:** {ad_pack}")

    st.markdown("### Why this is the right fit")
    st.write(ad_pack_help[ad_pack]["why"])

    st.markdown("### Easy way to explain it to the customer")
    st.success(ad_pack_help[ad_pack]["sales_line"])

    if notes:
        st.markdown("### Extra Notes")
        st.write(notes)