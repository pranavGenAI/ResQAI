import streamlit as st
import requests

st.title("Get User Location")

# Get coordinates
latitude = st.number_input("Latitude", format="%.6f")
longitude = st.number_input("Longitude", format="%.6f")

if st.button("Get Address"):
    api_key = "ab5b5ba90347427cb889b0b4c136e0bf"
    url = f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={api_key}"

    response = requests.get(url)
    data = response.json()

    if response.status_code == 200 and data["results"]:
        address = data["results"][0]["formatted"]
        st.success(f"Address: {address}")
    else:
        st.warning("Address not found.")
