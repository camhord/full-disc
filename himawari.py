import sys
import requests
import json
import shutil
from datetime import datetime
import cv2
import numpy
from io import BytesIO
import time
import concurrent.futures
import threading

BASE_URL = "http://himawari8-dl.nict.go.jp/himawari8/img"
WIDTH = 550
VISIBLE_LIGHT = "D531106"
INFRARED = "INFRARED_FULL"
DEPTHS = (1, 4, 8, 16, 20)

ZOOM_INDEX = 0
if len(sys.argv) > 1:
    ZOOM_INDEX = int(sys.argv[1]) if int(sys.argv[1]) < len(DEPTHS) else 0

blocks = DEPTHS[ZOOM_INDEX]

def get_himawari_datetime():
    latest_url = "https://himawari-8.appspot.com/latest"
    response = requests.get(latest_url)
    himawari_time = datetime.strptime(json.loads(response.text)["date"], "%Y-%m-%d %H:%M:%S")
    return himawari_time

def get_and_show(query_time):
    url = "/".join((BASE_URL, VISIBLE_LIGHT, "{}d".format(blocks), str(WIDTH), query_time.strftime("%Y/%m/%d/%H%M%S")))

    output = [numpy.zeros((WIDTH, WIDTH, 3), numpy.uint8) * blocks] * blocks
    imglock = threading.Lock()

    xvalues = list(range(blocks)) * blocks
    yvalues = list(range(blocks)) * blocks
    yvalues.sort()

    def download_and_merge(x, y):
        block_url = url + "_{}_{}.png".format(x, y) 
        print(block_url)
        response = requests.get(block_url)

        if not response.ok: 
            print(response)
        else:
            imageblock = BytesIO(response.content)
            with imglock:
                output[x][y] = cv2.imdecode(numpy.fromstring(imageblock.read(), numpy.uint8), 1)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(download_and_merge, xvalues, yvalues)

    return output

oldtime = datetime(1970,1,1,0,0,0,0)
#while True:
latest = get_himawari_datetime()

#if latest.timestamp() > oldtime.timestamp():
    #oldtime = latest
output = get_and_show(latest)
if blocks > 1:
    cvs = map(cv2.hconcat, output)
    disc = cv2.vconcat(cvs)
    cv2.imshow("ass", disc)
else:
    cv2.imshow("ass", output[0][0])
    cv2.waitKey(1)

    time.sleep(10)
        #output.save("himawari.png")
        #output.show("Himawari 8 | {}".format(latest.strftime("%Y-%m-%d %H:%M:%S")))
    
    #time.sleep(300)
