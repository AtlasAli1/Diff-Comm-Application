import streamlit as st

# Minimal Streamlit app for testing
st.title("✅ Minimal Streamlit Test")
st.write("If you can see this, Streamlit is working!")
st.success("Success! The application is running correctly.")

if st.button("Click me!"):
    st.balloons()
    st.write("🎉 Button works!")

st.write("---")
st.write("**Next Steps:**")
st.write("1. ✅ This minimal app works")
st.write("2. 🔄 Try the main Commission Calculator Pro")
st.write("3. 🚀 Access the full application")

# Show some basic info
st.write("**System Info:**")
st.write(f"- Streamlit version: {st.__version__}")
st.write(f"- Python version: {st.runtime.get_instance().get_python_version() if hasattr(st.runtime.get_instance(), 'get_python_version') else 'N/A'}")

st.write("**If this works, the main app should work too!**")