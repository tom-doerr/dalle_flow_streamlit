from docarray import Document
import streamlit as st
import time
# from PIL import Image
# import requests
import plotly.graph_objects as go

DEFAULT_SERVER_URL = 'grpc://dalle-flow.jina.ai:51005' 
if 'SERVER_URL' in st.secrets:
    SERVER_URL = st.secrets['SERVER_URL']
else:
    SERVER_URL = DEFAULT_SERVER_URL

LOGO_PATH = 'res/logo.png'
LOG_FILE = 'stats.csv'

# set the logo and title
st.set_page_config(page_title="DALL·E Flow Streamlit", initial_sidebar_state="auto", page_icon="res/logo.png")


col1, col2, col3 = st.columns([10,1,10])
with col1:
    st.title('DALL·E Flow')

with col2:
    st.write("")

with col3:
    st.image(LOGO_PATH, width=200)
    st.markdown('[GitHub Repo](https://github.com/tom-doerr/dalle_flow_streamlit)')

num_images = st.sidebar.slider('Number of initial images', 1, 9, 9)
skip_rate = 1 - st.sidebar.slider('Variations change amount', 0.0, 1.0, 0.5)




st.markdown('Example description: `A raccoon astronaut with the cosmos reflecting on the glass of his helmet dreaming of the stars, digital art`')
logo_description = st.text_input('Image description:')



def write_page_load_stats():
    with open(LOG_FILE, 'a') as f:
        f.write(f'{time.time()}\n')


def plot_page_load_stats():
    st.title('Page load stats')
    with st.spinner('Loading page load stats...'):
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()

        times = [float(line.strip()) for line in lines]
        times = sorted(times)
        num_times = len(times)
        first_time = times[0]
        first_time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_time))
        st.write(f'{num_times} page loads since {first_time_formatted}')

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) for t in times], y=[i for i in range(num_times)], mode='lines+markers'))
        st.plotly_chart(fig)



show_stats = st.sidebar.button('Show page load stats')

HTML_COUNT_WIDGET = '<img src="https://badges.pufler.dev/visits/tom-doerr/dummy1?style=for-the-badge&color=ff4b4b&logoColor=white&labelColor=302D41"/>'
# st.sidebar.markdown(HTML_COUNT_WIDGET, unsafe_allow_html=True)

write_page_load_stats()

if show_stats:
    plot_page_load_stats()

if not logo_description:
    st.stop()


prompt = logo_description

def get_images(prompt, num_images):
    try:
        return Document(text=prompt).post(SERVER_URL, parameters={'num_images': num_images}).matches
    except BlockingIOError as e:
        st.write(e)
        st.stop()

def display_images(images):
    for i, image in enumerate(images):
        # d:
        # <Document ('id', 'adjacency', 'mime_type', 'text', 'uri', 'tags') at f98709a922457dea22a7f19d398e3977>
        col_left, col_right = st.columns([1,1])
        with col_left:
            st.image(image.uri)
        with col_right:
            st.button('Create variations', key=image.uri, on_click=diffuse_image, args=(image,))
            st.button('Create high resolution version', key=image.uri, on_click=upscale_image, args=(image,))


def create_initial_image(prompt):
    start_time = time.time()
    with st.spinner('Creating the images. This may take over 10 minutes...'):
        images = get_images(prompt, num_images)
    end_time = time.time()
    st.write(f'Took {end_time - start_time:.1f} seconds')
    print(f'Took {end_time - start_time:.1f} seconds')

    display_images(images)
    st.balloons()

def diffuse_image(chosen_image):
    st.title('Image variations')
    with st.spinner('Creating variations, this may take a few minutes...'):
        diffused_images = chosen_image.post(f'{SERVER_URL}', parameters={'skip_rate': skip_rate, 'num_images': 9}, target_executor='diffusion').matches

    display_images(diffused_images)
    st.stop()


def upscale_image(chosen_image):
    st.title('High resolution image')
    with st.spinner('Creating a high resolution image from the selected image, this may take a few minutes...'):
        upscaled_image = chosen_image.post(f'{SERVER_URL}/upscale', target_executor='upscaler')
    st.image(upscaled_image.uri)
    st.stop()

def download_image(chosen_image):
    st.title('Downloading image')
    st.download_button(chosen_image.uri, chosen_image.uri, mime=chosen_image.mime_type)

    st.stop()



create_initial_image(prompt)
