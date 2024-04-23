from asyncio import sleep
import os
import requests
import subprocess
import time 



def start(file_path):
  time.sleep(5)
  subprocess.run(['python', file_path])




def fetch_data_from_api(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch data from API: {response.status_code}")
        return None

def save_data_to_file(filename, data):
    with open(filename, 'w') as file:
        file.write(data)

def read_last_post_number(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            last_post_number = int(file.read())
    else:
        last_post_number = 1  # Initialize to 1 if file doesn't exist
    return last_post_number

def update_last_post_number(filename, last_post_number):
    with open(filename, 'w') as file:
        file.write(str(last_post_number))

if __name__ == "__main__":
    base_api_url = "https://873273e1-c9c5-4959-9936-e1824681e748-00-3e51lgwuyc1e3.pike.replit.dev/view/card/"
    num_txt = "num.txt"



    last_post_number = read_last_post_number(num_txt)
    api_url = f"{base_api_url}{last_post_number}"

    data_from_api = fetch_data_from_api(api_url)
    if data_from_api:
        save_data_to_file("3n.txt", data_from_api)
        print(f"Data from post {last_post_number} saved to save.txt")

        next_post_number = last_post_number + 1
        update_last_post_number(num_txt, next_post_number)
        start("main.py")




