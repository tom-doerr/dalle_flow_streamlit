from docarray import Document
import streamlit as st
import time
# from PIL import Image
# import requests
import plotly.graph_objects as go
import grpc
import os

DEFAULT_SERVER_URL = 'grpc://dalle-flow.jina.ai:51005' 
if 'SERVER_URL' in st.secrets:
    SERVER_URL = st.secrets['SERVER_URL']
else:
    SERVER_URL = DEFAULT_SERVER_URL

LOGO_PATH = 'res/logo.png'
LOG_FILE_LOAD_STATS = 'stats.csv'
PROMPTS_LOG_CSV = 'propmts.csv'



if 'prompt' in st.experimental_get_query_params():
    prompt_in_url = st.experimental_get_query_params()['prompt'][0]
else:
    prompt_in_url = None


if not prompt_in_url:
    st.set_page_config(page_title="DALL·E Flow Streamlit", initial_sidebar_state="auto", page_icon="res/logo.png")
else:
    st.set_page_config(page_title=prompt_in_url, initial_sidebar_state="collapsed", page_icon="res/logo.png")





if not prompt_in_url:
    col1, col2, col3 = st.columns([10,1,10])
else:
    col1, col2, col3 = st.columns([10,1,1])

with col1:
    if not prompt_in_url:
        st.title('DALL·E Flow')
    else:
        st.title(f'Images of {prompt_in_url}')

with col2:
    st.write("")

with col3:
    if not prompt_in_url:
        st.image(LOGO_PATH, width=200)
    st.markdown('[GitHub Repo](https://github.com/tom-doerr/dalle_flow_streamlit)')

num_images = st.sidebar.slider('Number of initial images', 1, 9, 9)
skip_rate = 1 - st.sidebar.slider('Variations change amount', 0.0, 1.0, 0.5)


# with open(LOGO_PATH, 'rb') as f:
# with open('test_image.png', 'rb') as f:
    # logo = f.read()

# example str: data:image/png;charset=utf-8,%89PNG%0D%0A%1A
# logo_str = f'data:image/png;charset=utf-8,{logo.decode("utf-8")}'
# fix UnicodeDecodeError: 'utf-8' codec can't decode byte 0x89 in position 0: invalid start byte
# logo_str = f'data:image/png;charset=utf-8,{logo.decode("latin-1")}'








def write_page_load_stats():
    with open(LOG_FILE_LOAD_STATS, 'a') as f:
        f.write(f'{time.time()}\n')


def log_prompt(prompt):
    with open(PROMPTS_LOG_CSV, 'a') as f:
        f.write(f'{time.time()},{prompt}\n')


def plot_page_load_stats():
    with st.spinner('Loading page load stats...'):
        with open(LOG_FILE_LOAD_STATS, 'r') as f:
            lines = f.readlines()

        times = [float(line.strip()) for line in lines]
        times = sorted(times)
        num_times = len(times)
        first_time = times[0]
        first_time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_time))
        # st.write(f'{num_times} page loads since {first_time_formatted}')
        st.write(f'{num_times} page loads')

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) for t in times], y=[i for i in range(num_times)], mode='lines+markers'))
        st.plotly_chart(fig, use_container_width=True)


# def load_prompts():
    # # check if file exists
    # if not os.path.isfile(PROMPTS_LOG_CSV):
        # return []
    # with open(PROMPTS_LOG_CSV, 'r') as f:
        # lines = f.readlines()

    # lines = [line.strip().split(',') for line in lines]
    # lines = [line for line in lines if len(line) == 2]
    # lines = [line for line in lines if line[1] != '']
    # lines = [line[1] for line in lines]
    # return lines

def load_prompts_with_times():
    if not os.path.isfile(PROMPTS_LOG_CSV):
        return []
    with open(PROMPTS_LOG_CSV, 'r') as f:
        lines = f.readlines()

    lines = [line.strip().split(',') for line in lines]
    lines = [line for line in lines if len(line) == 2]
    lines = [line for line in lines if line[1] != '']
    lines = [line for line in lines if line[0] != '']

    return lines

def load_prompts_with_times_unique():
    prompts_with_times = load_prompts_with_times()
    output = []
    prompts_set = set()
    for prompt_with_time in prompts_with_times:
        if prompt_with_time[1] not in prompts_set:
            output.append(prompt_with_time)
            prompts_set.add(prompt_with_time[1])

    return output



def load_prompts():
    lines = load_prompts_with_times()
    lines = [line[1] for line in lines]
    return lines



def load_prompts_unique():
    prompts_all = load_prompts()
    prompts_unique = set(prompts_all)
    return prompts_unique


def plot_prompts_stats(prompts):
    with st.spinner('Loading prompts stats...'):

        times = [float(line[0].strip()) for line in prompts]
        times = sorted(times)
        num_times = len(times)
        first_time = times[0]
        first_time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_time))
        # st.write(f'{num_times} prompts since {first_time_formatted}')
        st.write(f'{num_times} prompts')

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) for t in times], y=[i for i in range(num_times)], mode='lines+markers'))
        st.plotly_chart(fig, use_container_width=True)





def show_stats():
    # add stats to url
    st.experimental_set_query_params(stats='true')
    plot_page_load_stats()

    num_prompts = len(load_prompts())
    prompts_with_times = load_prompts_with_times()
    plot_prompts_stats(prompts_with_times)

    num_unique_prompts = len(load_prompts_unique())
    prompts_with_times_unique = load_prompts_with_times_unique()
    plot_prompts_stats(prompts_with_times_unique)


def get_images(prompt, num_images):
    try:
        return Document(text=prompt).post(SERVER_URL, parameters={'num_images': num_images}).matches
    # except BlockingIOError as e:
    except grpc.aio._call.AioRpcError as e:
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
    print(f'id: {images[0].id}')
    print(f'adjacency: {images[0].adjacency}')
    print(f'mime_type: {images[0].mime_type}')
    print(f'text: {images[0].text}')
    # print(f'uri: {images[0].uri}')
    print(f'tags: {images[0].tags}')
    end_time = time.time()
    st.write(f'Took {end_time - start_time:.1f} seconds')
    print(f'Took {end_time - start_time:.1f} seconds')

    display_images(images)
    st.balloons()





def diffuse_image(chosen_image):
    st.title('Image variations')
    # if True:
    if False:
        st.warning('Overwritting chosen image!')
        chosen_image.uri = logo_str
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


def get_num_prompts_last_x_min(mins):
    prompts_with_times = load_prompts_with_times()
    prompts_with_times = [prompt_with_time for prompt_with_time in prompts_with_times if time.time() - float(prompt_with_time[0]) < mins * 60]
    num_prompts = len(prompts_with_times)
    print(f'{num_prompts} prompts in the last {mins} minutes')
    return num_prompts






if not prompt_in_url:
    prompt = logo_description
else:
    prompt = prompt_in_url

show_stats_bool = (st.sidebar.button('Show statistics') or (('stats' in st.experimental_get_query_params())  and st.experimental_get_query_params()['stats'][0] == 'true'))
if st.sidebar.button('Add prompt to URL'):
    st.experimental_set_query_params(prompt=prompt)
    # st.experimental_set_query_params(prompt='hamster in speedo')

HTML_COUNT_WIDGET = '<img src="https://badges.pufler.dev/visits/tom-doerr/dummy1?style=for-the-badge&color=ff4b4b&logoColor=white&labelColor=302D41"/>'
# st.sidebar.markdown(HTML_COUNT_WIDGET, unsafe_allow_html=True)

write_page_load_stats()

if show_stats_bool:
    show_stats()



if get_num_prompts_last_x_min(10) >= 2:
    st.info('The server currently gets a high number of requests and is overloaded, please try again later.')
    st.stop()

if not prompt_in_url:
    st.markdown('Example description: `A raccoon astronaut with the cosmos reflecting on the glass of his helmet dreaming of the stars, digital art`')
    logo_description = st.text_input('Image description:')



if not prompt:
    st.stop()


log_prompt(prompt)
