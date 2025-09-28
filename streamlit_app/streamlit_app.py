import streamlit as st
import requests

st.title("Housing Price Prediction UI")

suburb = st.text_input("Suburb", "Richmond")
bedrooms = st.number_input("Number of bedrooms", 1, 10, 3)
bathrooms = st.number_input("Number of bathrooms", 1, 5, 2)
car_park = st.number_input("Car parks", 0, 5, 1)

if st.button("Predict"):
    payload = {
        "suburb": suburb,
        "number_of_bedroom": bedrooms,
        "bathroom": bathrooms,
        "car_park": car_park
    }
    response = requests.post("http://backend:8000/predict", json=payload)
    if response.status_code == 200:
        result = response.json()
        st.success(f"Predicted price: {result['prediction']}")
    else:
        st.error("Backend error, check logs.")
