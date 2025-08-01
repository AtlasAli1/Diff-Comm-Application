import streamlit as st

st.set_page_config(
    page_title="Test App",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Test Application")
st.success("✅ Application is running successfully!")

# Test basic functionality
if st.button("Test Button"):
    st.balloons()
    st.write("Button clicked!")

# Test session state
if 'counter' not in st.session_state:
    st.session_state.counter = 0

if st.button("Increment Counter"):
    st.session_state.counter += 1

st.write(f"Counter: {st.session_state.counter}")

# Test import of our modules
try:
    from models import CommissionCalculator
    st.success("✅ Models import successfully")
except Exception as e:
    st.error(f"❌ Models import failed: {e}")

try:
    from utils import DatabaseManager
    st.success("✅ Utils import successfully")
except Exception as e:
    st.error(f"❌ Utils import failed: {e}")

# Show system info
st.subheader("System Information")
st.write("Streamlit is working correctly!")