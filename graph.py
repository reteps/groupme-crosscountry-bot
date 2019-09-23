#!/usr/bin/env python3

import requests, re, datetime, bs4, time, sys, json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, SecondLocator
from flask import Flask
from flask import request
import mebots


DEBUG = False
GROUPME_IMAGE_SERVICE_TOKEN = ""

app = Flask(__name__)
bot = mebots.Bot("crosscountrybot", os.environ["BOT_TOKEN"])

def plotTimes(group_id, data):
    formatter = DateFormatter('%m-%d-%y')
    x = data["x"]
    y = data["y"]
    _, axes = plt.subplots(1, data["years"], sharey=True)
    if len(data['boundaries']) == 0:
        sendMessage(group_id, text=f'{data["name"]} has no 5k races recorded.')
        return False

    if data["years"] == 1:
        axes = [axes]
    if DEBUG:
        print(f'Starting plot for {data["name"]}... ',end='')
    for i in range(data['years']):
        axes[i].plot(x, y)
        if i < data['years'] - 1:
            axes[i].spines['right'].set_visible(False)
        if i > 0:
            axes[i].spines['left'].set_visible(False)
            axes[i].yaxis.set_ticks_position('none')
        axes[i].set_xlim(data['boundaries'][i]['start'],data['boundaries'][i]['end'])
        plt.sca(axes[i])
        plt.xticks(rotation=65)
        plt.rc('axes', labelsize=8)
        axes[i].xaxis.set_major_formatter(formatter)
        axes[i].grid(linestyle="dashed",linewidth=0.5)
        loc = SecondLocator(interval=15)
        axes[i].yaxis.set_major_locator(loc)
        axes[i].yaxis.set_major_formatter(DateFormatter('%M:%S'))
        for label in (axes[i].get_xticklabels()):
            label.set_fontsize(7)

        #axes[i].get_xticklabels().set_fontsize(10)
    if DEBUG:
        print('done.')
    try:
        plt.sca(axes[0])
    except IndexError:
        sendMessage(group_id, text=f"{data['name']} has no times recorded.")
        return False
    plt.xlabel('Date')
    plt.ylabel('5k Time')
    plt.sca(axes[int(data['years']/2)])
    plt.title(data['name'])
    if DEBUG:
        print('Try to save figure... ',end='')
    plt.savefig('plot.png', format="png")
    plt.close()
    if DEBUG:
        print('done.')

    return True
def uploadImage():
    headers = {
        'X-Access-Token': GROUPME_IMAGE_SERVICE_TOKEN
    }
    files = {
            'file': open('plot.png','rb'),
            'Content-Type': 'image/png'
    }
    r = requests.post("https://image.groupme.com/pictures",headers=headers,files=files)
    return r.json()["payload"]["url"]
def getRunnerId(name):
    data = {'q':name,'fq':'t:a l:4','start':0}
    r = requests.post("https://www.athletic.net/Search.aspx/runSearch", json=data)
    matches = re.findall("AID=\d{4,9}", r.text)
    return matches[0]

def getTimes(runner_id):
    url = f"https://www.athletic.net/CrossCountry/Athlete.aspx?{runner_id}"
    if DEBUG:
        print(url)
    r = requests.get(url)
    soup = bs4.BeautifulSoup(r.text, "lxml")
    name = soup.find("h2",class_="mt-2").find("span", class_="mr-2").text
    data = {"x":[],"y":[],"name":name,"boundaries":{}}
    # get high school seasons
    seasons = soup.select("div.season.L4")
    data["years"] = len(seasons)
    y = len(seasons) - 1
    for i in reversed(range(len(seasons))):

        tag = seasons[i].find("h5",text="5,000 Meters")
        if tag == None:
            continue
        table = tag.next_sibling
        year = seasons[i]["class"][4][1:]
        races = table.findAll("tr")
        data["boundaries"][y - i] = {}
        for j in range(len(races)):
            raw_time = races[j].find("td",{"style":"width: 105px;"}).find("a").text.lower()
            time_regex = re.sub("pr|sr| ","",raw_time)
            time = datetime.datetime.strptime(time_regex, "%M:%S.%f")
            raw_date = races[j].find("td",{"style":"width: 60px;"}).text
            if DEBUG:
                print(time_regex, raw_date)
            date = datetime.datetime.strptime(f"{raw_date}, {year}", "%b %d, %Y")
            data["x"].append(date)
            data["y"].append(time)
            if j == 0:
                data["boundaries"][y - i]["start"] = date - datetime.timedelta(days=5)

        data["boundaries"][y - i]["end"] = data["x"][-1] + datetime.timedelta(days=5)

    if DEBUG:
        print(json.dumps(data, default=str, sort_keys=True, indent=4))
    return data
def sendMessage(group_id, img="",text=""):
    data = {
        "bot_id": bot.instance(group_id).id,
        "text":text,
        "picture_url":img
    }
    if DEBUG:
        print(data)
        return
    requests.post("https://api.groupme.com/v3/bots/post", json=data)

@app.route('/message', methods=['POST'])
def message():
    data = request.get_json()
    text = data['text'].lower()
    print(text)
    if text.startswith("graph") and len(text.split(" ")) > 1:
        name = " ".join(text.split(" ")[1:])
        id = getRunnerId(name)
        data = getTimes(id)
        success = plotTimes(data['group_id'], data)
        if success:
            url = uploadImage()
            if DEBUG:
                print('Upload successful.')
            sendMessage(data['group_id'], img=url)
    return "OK"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
