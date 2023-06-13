import os
import sys
import yaml
from image_gen import ImageGen
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# TODO: logging
# TODO: image name is right?
# TODO: Testing!
# TODO: streamlit - doing
# TODO: Přístup přes file browser i last image
# TODO: Button poslat na mail

image_urls = [
    'https://images.saymedia-content.com/.image/t_share/MTkwODkzODUwNDE4OTQ3NjY5/everything-you-wanted-to-know-about-dall-e-2-the-amazing-ai-artist.jpg',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',
    'https://images.saymedia-content.com/.image/t_share/MTkwODkzODUwNDE4OTQ3NjY5/everything-you-wanted-to-know-about-dall-e-2-the-amazing-ai-artist.jpg',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',
    'https://miro.medium.com/v2/resize:fit:1024/1*e2-GB_Hdylczkj5PHh-lJQ.png',

]


def init_st():
    st.set_page_config(
        page_icon="🧊",
        layout="wide",
        initial_sidebar_state="expanded")

    st.title("Enhance your photo with AI")

    hide_img_fs = '''
    <style>
    button[title="View fullscreen"]{
        visibility: hidden;}
    a{visibility:hidden;}
    body{background-color:white}
    button {
        min-width: 200px;
    }
    img {
    max-width:200px}
    
    </style>
    '''


    st.markdown(hide_img_fs, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2,1,2,2], gap="small")
    with col1:
        image1 = Image.open("presets/template_1.png")
        st.image(image1, use_column_width=True, width=150)
        load_button = st.button("Upload")
    with col2:
        pass
    with col3:
        image2 = Image.open("presets/template_2.jpg")
        st.image(image1, use_column_width=True, width=150)
        gen_button = st.button("Generate")

    with col4:
        button1_clicked = st.button("Send to email")
        button2_clicked = st.button("Print")

    st.header("Presets:")
    imageCarouselComponent = components.declare_component \
        ("image-carousel-component", path="src/frontend/public")

    # if button1_clicked:
    #     image_gen.gen_image(prompt="blablabla")
    #     image_gen.save_image()
    #
    # if button2_clicked:
    #     print("button2 clicked")

    selectedImageUrl = imageCarouselComponent(imageUrls=image_urls, height=200,)


def load_config(path: str) -> dict:
    with open(path, 'r') as file:
        return yaml.safe_load(file)


def main():
    init_st()


if __name__ == "__main__":
    conf = load_config("configs/conf.yaml")
    creds = load_config("configs/creds.yaml")

    image_gen = ImageGen(key=creds["DEEPAI_API_KEY"], conf=conf)

    sys.exit(main())
