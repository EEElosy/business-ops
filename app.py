import streamlit as st

st.title("🏭 My Engineering Business Ops")
st.write("If you can see this on your phone, the system works!")

# A simple interactive element to test
name = st.text_input("Who is the CEO?")
if name:
    st.success(f"Welcome, Boss {name}!")