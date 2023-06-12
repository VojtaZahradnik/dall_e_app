import streamlit as st
import streamlit.components.v1 as components
import os

image_urls = [
    'https://images.saymedia-content.com/.image/t_share/MTkwODkzODUwNDE4OTQ3NjY5/everything-you-wanted-to-know-about-dall-e-2-the-amazing-ai-artist.jpg',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',
    'https://images.saymedia-content.com/.image/t_share/MTkwODkzODUwNDE4OTQ3NjY5/everything-you-wanted-to-know-about-dall-e-2-the-amazing-ai-artist.jpg',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',

]

st.title("Adastra AI generated images")

st.header("Presets:")

imageCarouselComponent = components.declare_component\
    ("image-carousel-component", path="src/frontend/public")

selectedImageUrl = imageCarouselComponent(imageUrls=image_urls, height=200)

st.header("Prompt:")

user_input = st.text_input("Enter your text:")

st.write("You entered:", user_input)

col1, col2 = st.columns(2)

# Button 1 in the first column
button1_clicked = col1.button("Generate")

# Button 2 in the second column
button2_clicked = col2.button("Print")

if selectedImageUrl is not None:
    st.image(selectedImageUrl)