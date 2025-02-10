import streamlit as st
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim
import requests

st.title("Get User Location in Streamlit")

location = get_geolocation()

if location:
    lat, lon = location["coords"]["latitude"], location["coords"]["longitude"]
    st.success(f"Latitude: {lat}, Longitude: {lon}")
else:
    st.warning("Click the button and allow location access.")


# Get coordinates
latitude = lat
longitude = lon

api_key = "ab5b5ba90347427cb889b0b4c136e0bf"
url = f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={api_key}"
response = requests.get(url)
data = response.json()
if response.status_code == 200 and data["results"]:
    address = data["results"][0]["formatted"]
    st.success(f"Address: {address}")
else:
    st.warning("Address not found.")
