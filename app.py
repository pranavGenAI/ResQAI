import streamlit as st
from streamlit_javascript import st_javascript
from geopy.geocoders import Nominatim

st.title("Get User Location in Streamlit")

# JavaScript to get location
location = st_javascript("""
    navigator.geolocation.getCurrentPosition((position) => {
        const coords = { 
            latitude: position.coords.latitude, 
            longitude: position.coords.longitude 
        };
        document.body.setAttribute('data-location', JSON.stringify(coords));
    });

    new Promise((resolve) => {
        setTimeout(() => {
            resolve(document.body.getAttribute('data-location'));
        }, 1000);
    });
""")

if location:
    st.success(f"Location Data: {location}")
    
    # Convert to dictionary
    import json
    loc_data = json.loads(location)
    lat, lon = loc_data["latitude"], loc_data["longitude"]
    
    st.write(f"Latitude: {lat}, Longitude: {lon}")

    # Reverse geocoding to get address
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse((lat, lon), language="en")

    if location:
        st.write(f"Address: {location.address}")
else:
    st.warning("Allow location access in your browser.")

