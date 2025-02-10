import streamlit as st
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim

st.title("Get User Location in Streamlit")

location = get_geolocation()

if location:
    lat, lon = location["coords"]["latitude"], location["coords"]["longitude"]
    st.success(f"Latitude: {lat}, Longitude: {lon}")

    geolocator = Nominatim(user_agent="geoapiExercises")
    address = geolocator.reverse((lat, lon), language="en")

    if address:
        st.write(f"Address: {address.address}")
else:
    st.warning("Click the button and allow location access.")
