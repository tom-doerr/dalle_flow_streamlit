from docarray import Document
import streamlit as st
import time
# from PIL import Image
# import requests
import plotly.graph_objects as go
import grpc
import os

import pymongo

DEFAULT_SERVER_URL = 'grpc://dalle-flow.jina.ai:51005' 
if 'SERVER_URL' in st.secrets:
    SERVER_URL = st.secrets['SERVER_URL']
else:
    SERVER_URL = DEFAULT_SERVER_URL

LOGO_PATH = 'res/logo.png'
LOG_FILE_LOAD_STATS = 'stats.csv'
PROMPTS_LOG_CSV = 'propmts.csv'

if 'PRIMARY_CONNECTION_STRING' in st.secrets:
    PRIMARY_CONNECTION_STRING = st.secrets['PRIMARY_CONNECTION_STRING']
    db = pymongo.MongoClient(PRIMARY_CONNECTION_STRING).get_database('dalle-flow-streamlit')
else:
    db = None


def display_donation_badge():
    html_badge = '''
    <p align="center">
    <a href="https://www.buymeacoffee.com/TomDoerr" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
</p>
    '''
    st.markdown(html_badge, unsafe_allow_html=True)



def write_document(collection_link, document):
    if db:
        try:
            collection = db[collection_link]
            collection.insert_one(document)
            print('Document inserted')
        except Exception as e:
            print('Failed to insert document: {}'.format(e))
    else:
        print(f'No database connection, not inserting into {collection_link}')



def get_all_documents(collection_link):
    collection = db[collection_link]
    return_list = []
    for document in collection.find():
        return_list.append(document)
    return return_list


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



import psutil
import datetime
import sys

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    return psutil.virtual_memory().percent

def get_disk_usage():
    return psutil.disk_usage('/').percent



print(str(datetime.datetime.now()) + ": CPU: " + str(get_cpu_usage()) + "% RAM: " + str(get_ram_usage()) + "% DISK: " + str(get_disk_usage()) + "%")

sys.stdout.flush()



# with open(LOGO_PATH, 'rb') as f:
# with open('test_image.png', 'rb') as f:
    # logo = f.read()

# example str: data:image/png;charset=utf-8,%89PNG%0D%0A%1A
# logo_str = f'data:image/png;charset=utf-8,{logo.decode("utf-8")}'
# fix UnicodeDecodeError: 'utf-8' codec can't decode byte 0x89 in position 0: invalid start byte
# logo_str = f'data:image/png;charset=utf-8,{logo.decode("latin-1")}'








def write_page_load_stats():
    write_document('page_loads', {'time': time.time()})
    with open(LOG_FILE_LOAD_STATS, 'a') as f:
        f.write(f'{time.time()}\n')


def log_prompt(prompt):
    write_document('prompts', {'time': time.time(), 'prompt': prompt})
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


        st.write("Page loads DB:")
        page_loads = get_all_documents('page_loads')
        print(f'page_loads: {list(page_loads)}')

        # plot them
        times = [float(page_load['time']) for page_load in page_loads]
        times = sorted(times)
        num_times = len(times)
        first_time = times[0]
        first_time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_time))
        # st.write(f'{num_times} page loads since {first_time_formatted}')
        st.write(f'{num_times} page loads')

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) for t in times], y=[i for i in range(num_times)], mode='lines+markers'))
        st.plotly_chart(fig, use_container_width=True)


        overloaded_times_document = get_all_documents('overloaded')
        overloaded_times = [float(overloaded_time['time']) for overloaded_time in overloaded_times_document]
        overloaded_times = sorted(overloaded_times)
        num_overloaded_times = len(overloaded_times)
        first_overloaded_time = overloaded_times[0]
        first_overloaded_time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_overloaded_time))

        st.write("Overloaded times:")
        st.write(f'{num_overloaded_times} times')

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) for t in overloaded_times], y=[i for i in range(num_overloaded_times)], mode='lines+markers'))
        st.plotly_chart(fig, use_container_width=True)


        # from the collection initial_images get the duration for each entry using the db object
        durations_raw = db.initial_images.find({}, {'time': 1, 'duration': 1})
        # print("durations_raw:", list(durations_raw))
        durations = [{'time': float(duration['time']), 'duration': float(duration['duration'])} for duration in durations_raw]
        durations = sorted(durations, key=lambda x: x['time'])
        num_durations = len(durations)
        first_duration = durations[0]['time']
        first_duration_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_duration))
        st.write("Durations initial:")

        fig = go.Figure()
        # use points instead of lines
        fig.add_trace(go.Scatter(x=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d['time'])) for d in durations], y=[d['duration'] for d in durations], mode='markers'))
        st.plotly_chart(fig, use_container_width=True)


        # from the collection diffusion_images get the duration for each entry using the db object
        diffusion_image_durations_raw = db.diffusion_images.find({}, {'time': 1, 'duration': 1})
        diffusion_image_durations = [{'time': float(diffusion_image_duration['time']), 'duration': float(diffusion_image_duration['duration'])} for diffusion_image_duration in diffusion_image_durations_raw if 'duration' in diffusion_image_duration]
        diffusion_image_durations = sorted(diffusion_image_durations, key=lambda x: x['time'])
        num_diffusion_image_durations = len(diffusion_image_durations)
        first_diffusion_image_duration = diffusion_image_durations[0]['time']
        first_diffusion_image_duration_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_diffusion_image_duration))
        st.write("Durations diffusion:")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d['time'])) for d in diffusion_image_durations], y=[d['duration'] for d in diffusion_image_durations], mode='markers'))
        st.plotly_chart(fig, use_container_width=True)


        # plot number of diffusions
        diffusion_times_raw = db.diffusion_images.find({}, {'time': 1})
        diffusion_times = [float(diffusion_time['time']) for diffusion_time in diffusion_times_raw]
        diffusion_times = sorted(diffusion_times)
        num_diffusion_times = len(diffusion_times)
        first_diffusion_time = diffusion_times[0]
        first_diffusion_time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_diffusion_time))
        st.write("Diffusions:")
        st.write(f'{num_diffusion_times} diffusions')

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d)) for d in diffusion_times], y=[i for i in range(num_diffusion_times)], mode='lines+markers'))
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
    st.write('Prompts:')
    plot_prompts_stats(prompts_with_times)

    num_unique_prompts = len(load_prompts_unique())
    prompts_with_times_unique = load_prompts_with_times_unique()
    st.write('Unique prompts:')
    plot_prompts_stats(prompts_with_times_unique)


def get_images(prompt, num_images):
    try:
        if use_dalle and use_diffusion:
            target_executor = None
        elif use_dalle:
            target_executor = 'dalle'
        elif use_diffusion:
            target_executor = 'diffusion'
        else:
            st.info('No AI selected. Please select an AI to use in the sidebar.')
            st.stop()
        return Document(text=prompt).post(SERVER_URL, parameters={'num_images': num_images}, target_executor=target_executor).matches
    # except BlockingIOError as e:
    except grpc.aio._call.AioRpcError as e:
        st.write(e)
        st.stop()


def display_image_with_buttons(image):
    col_left, col_right = st.columns([1,1])
    with col_left:
        st.image(image.uri)
    with col_right:
        st.button('Create variations', key=image.uri, on_click=diffuse_image, args=(image,))
        st.button('Create high resolution version', key=image.uri, on_click=upscale_image, args=(image,))


def display_images(images, original=None):
    if original:
        images.append(original)
    for i, image in enumerate(images):
        if original and i == len(images) - 1:
            st.write('---')
            st.write('Original image:')
        # d:
        # <Document ('id', 'adjacency', 'mime_type', 'text', 'uri', 'tags') at f98709a922457dea22a7f19d398e3977>
        display_image_with_buttons(image)

    st.write('---')
    display_donation_badge()


  

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
    if False:
        import urllib.request
        images_data = []
        # download images
        for image in images:
            urllib.request.urlretrieve(image.uri, f'{image.id}.png')
            images_data.append(urllib.request.urlopen(image.uri).read())

    else:
        # images_data = images
        # images_data = [image.uri for image in images]
        images_data = [convert_image_to_dict(image) for image in images]
    write_document('initial_images', {'time': time.time(), 'num_images': num_images, 'prompt': prompt, 'duration': end_time - start_time, 'images': images_data})
    # display_images(images)
    st.balloons()



def convert_image_to_dict(image):
    return {'id': image.id, 'adjacency': image.adjacency, 'mime_type': image.mime_type, 'text': image.text, 'uri': image.uri, 'tags': image.tags}


def diffuse_image(chosen_image):
    st.title('Image variations')
    # if True:
    if False:
        st.warning('Overwritting chosen image!')
        chosen_image.uri = logo_str
    with st.spinner('Creating variations, this may take a few minutes...'):
        NUM_IMAGES_DIFFUSION = 9
        start_time = time.time()
        diffused_images = chosen_image.post(f'{SERVER_URL}', parameters={'skip_rate': skip_rate, 'num_images': NUM_IMAGES_DIFFUSION}, target_executor='diffusion').matches
        end_time = time.time()

    display_images(diffused_images, chosen_image)
    # <Document ('id', 'adjacency', 'mime_type', 'text', 'uri', 'tags', 'scores')
    image_dict = convert_image_to_dict(chosen_image)
    image_dicts = [convert_image_to_dict(image) for image in diffused_images]
    duration = end_time - start_time
    write_document('diffusion_images', {'time': time.time(), 'skip_rate': skip_rate, 'num_images': NUM_IMAGES_DIFFUSION, 'prompt': prompt, 'duration': duration, 'chosen_image': image_dict, 'diffused_images': image_dicts})

    st.balloons()
    st.stop()


def upscale_image(chosen_image):
    st.title('High resolution image')
    with st.spinner('Creating a high resolution image from the selected image, this may take a few minutes...'):
        upscaled_image = chosen_image.post(f'{SERVER_URL}/upscale', target_executor='upscaler')
    st.image(upscaled_image.uri)
    # display_images([upscaled_image], original=chosen_image)
    st.write('---')
    st.write('Original image:')
    display_image_with_buttons(chosen_image)
    image_chosen_dict = convert_image_to_dict(chosen_image)
    image_upscaled_dict = convert_image_to_dict(upscaled_image)
    write_document('upscaled_images', {'time': time.time(), 'chosen_image': image_chosen_dict, 'upscaled_image': image_upscaled_dict})
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




st.sidebar.write('AIs to use')
use_dalle = st.sidebar.checkbox('DALL·E Mega', value=True)
use_diffusion = st.sidebar.checkbox('GLID3 XL', value=False)

st.sidebar.write('---')


show_stats_bool = (st.sidebar.button('Show statistics') or (('stats' in st.experimental_get_query_params())  and st.experimental_get_query_params()['stats'][0] == 'true'))
if st.sidebar.button('Add prompt to URL'):
    st.experimental_set_query_params(prompt=prompt)
    # st.experimental_set_query_params(prompt='hamster in speedo')

HTML_COUNT_WIDGET = '<img src="https://badges.pufler.dev/visits/tom-doerr/dummy1?style=for-the-badge&color=ff4b4b&logoColor=white&labelColor=302D41"/>'
# st.sidebar.markdown(HTML_COUNT_WIDGET, unsafe_allow_html=True)

write_page_load_stats()

if show_stats_bool:
    show_stats()


MINUTES_TO_CONSIDER = 10
MAX_REQUESTS_PER_MINUTE = 2

num_prompts_last_x_min = get_num_prompts_last_x_min(MINUTES_TO_CONSIDER)

if num_prompts_last_x_min >= MAX_REQUESTS_PER_MINUTE:
    st.info('The server currently gets a high number of requests and is overloaded, please try again later.')
    write_document('overloaded', {'time': time.time(), 'num_prompts': num_prompts_last_x_min, 'max_requests_per_minute': MAX_REQUESTS_PER_MINUTE, 'mins_considered': MINUTES_TO_CONSIDER})
    st.stop()

if not prompt_in_url:
    st.markdown('Example description: `A raccoon astronaut with the cosmos reflecting on the glass of his helmet dreaming of the stars, digital art`')
    logo_description = st.text_input('Image description:')


if not prompt_in_url:
    prompt = logo_description
else:
    prompt = prompt_in_url



if not prompt:
    st.stop()


log_prompt(prompt)
create_initial_image(prompt)
