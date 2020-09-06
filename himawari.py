
import sys
import requests
import json
import shutil
from datetime import datetime
from PIL import Image
from io import BytesIO
import concurrent.futures
import threading

BASE_URL = "https://himawari8-dl.nict.go.jp/himawari8/img"
WIDTH = 550
VISIBLE_LIGHT = "D531106"
INFRARED = "INFRARED_FULL"
DEPTHS = (1, 4, 8, 16, 20)

ZOOM_INDEX = 0
if len(sys.argv) > 1:
    ZOOM_INDEX = int(sys.argv[1]) if int(sys.argv[1]) < len(DEPTHS) else 0

print(sys.argv)

def get_himawari_datetime():
    latest_url = "/".join((BASE_URL, VISIBLE_LIGHT, "latest.json"))
    response = requests.get(latest_url)
    himawari_time = datetime.strptime(json.loads(response.text)["date"], "%Y-%m-%d %H:%M:%S")
    return himawari_time.strftime("%Y/%m/%d/%H%M%S")

blocks = DEPTHS[ZOOM_INDEX]
time = get_himawari_datetime()
url = "/".join((BASE_URL, VISIBLE_LIGHT, "{}d".format(blocks), str(WIDTH), time))

output = Image.new('RGB', (WIDTH * blocks, WIDTH * blocks))
imglock = threading.Lock()

def download_and_merge(x, y):
    block_url = url + "_{}_{}.png".format(x, y)
    print(block_url)
    response = requests.get(block_url)

    if not response.ok:
        print(response)
    else:
        imageblock = response.content
        with imglock:
            output.paste(Image.open(BytesIO(imageblock)), (x * WIDTH, y * WIDTH))

# This is a bit of a hack, but I needed to combinatorially map all possible x and y pairs in the executor
# and I couldn't figure out another way to do it without manually ordering the values like this.
xvalues = list(range(blocks)) * blocks
yvalues = list(range(blocks)) * blocks
yvalues.sort()

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(download_and_merge, xvalues, yvalues)

output.save("himawari.png")