# -*- coding: utf-8 -*-
# !/usr/bin/python3

import json
import os
import subprocess
import sys
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service


def add2JDownloader(url):
    with open(os.devnull, 'w') as tempf:
        subprocess.run(["java", "-jar", JDjarFile, "-a", url], stdout=tempf, stderr=tempf)

    time.sleep(5)


def getPosts(post_hrefs):
    # Init Posts
    posts = {}
    vodOptions = []
    TIMEOUT = 10

    # Goto every post page
    for href in reversed(post_hrefs):
        browser.get(href + "?max-results=100")
        raceTitle = browser.title.replace("BurningWhee1s: ", "").replace(".", "")
        print(raceTitle)
        sessionTitle, sessionPost = "", {}

        # Get Post Body
        body = browser.find_element(By.CLASS_NAME, "post-body")

        # Goto through every elem -> filter
        for elem in body.find_elements(By.TAG_NAME, "*"):
            # Add text to raceTitle
            if elem.tag_name == "span":
                sessionTitle += elem.text + " "

            # Finish racePost
            if elem.tag_name == "select":
                sessionTitle = sessionTitle.replace(".", "").strip()

                # Goto through every option -> filter
                for option in elem.find_elements(By.TAG_NAME, "option"):
                    option = option.get_attribute("value")
                    sessionPost[sessionTitle] = "null" + "|" + href

                    if option not in vodOptions:
                        # Filter "best" option
                        if "streamtape" in option:
                            option = option.replace("streamtape.com/e/", "streamtape.com/v/")
                            req = requests.get(option, timeout=TIMEOUT)
                            if req.status_code == 200:
                                sessionPost[sessionTitle] = option
                                vodOptions.append(option)
                                break
                        if "mail.ru" in option:
                            req = requests.get(option, timeout=TIMEOUT)
                            if req.status_code == 200:
                                sessionPost[sessionTitle] = option
                                vodOptions.append(option)
                                break
                        if "vk.com" in option:
                            req = requests.get(option, timeout=TIMEOUT)
                            if req.status_code == 200:
                                contentText = req.text
                                if "foi removido de acesso" not in contentText and "video has been removed" not in contentText:
                                    sessionPost[sessionTitle] = option
                                    vodOptions.append(option)
                                    break

                # Reset
                sessionTitle = ""
                posts[raceTitle] = sessionPost
    return posts


def download():
    # Create JSON_REPORT
    JSON_REPORT, NULL_REPORT = {}, {}

    # Get all href posts
    print("post_hrefs")
    post_hrefs = [post.find_elements(By.TAG_NAME, "a")[0].get_attribute("href") for post in
                  browser.find_elements(By.CLASS_NAME, "post-title")]
    print("--------")

    # Get posts
    print("getPosts")
    posts = getPosts(post_hrefs)
    print("--------")

    # Go through every race
    formatIdx = "{:0" + str(len(str(len(posts.keys())))) + "}"
    for idx_r, raceTitle in enumerate(posts.keys()):
        idx_r = formatIdx.format(idx_r + 1)
        sessions = posts[raceTitle]

        # Check if the race as sessions
        if len(sessions) > 0:
            n_sessions = []
            raceTitle = idx_r + " - " + raceTitle
            print(raceTitle)
            if os.path.exists(os.path.join(COMPETITION_FOLDER, raceTitle)):
                print("Already downloaded")
                print()
                continue

            # Go through every session
            for idx_s, sessionTitle in enumerate(sessions.keys()):
                idx_s = formatIdx.format(idx_s + 1)
                sessionURL = sessions[sessionTitle]
                sessionTitle = idx_r + "." + idx_s + " - " + sessionTitle
                print(sessionTitle)
                if sessionURL[0:4] == "null":
                    NULL_REPORT[sessionTitle] = sessionURL[5::]
                else:
                    n_sessions.append(sessionTitle)
                    add2JDownloader(sessionURL)

            print("")

            # Add new sessions to JSON_REPORT
            JSON_REPORT[raceTitle] = n_sessions

    # Save report to file
    JSON_FILE = os.path.join(COMPETITION_FOLDER, "report.json")
    with open(JSON_FILE, 'w') as outfile:
        outfile.write(json.dumps(JSON_REPORT, indent=4))

    # Save null report to file if necessary
    if len(NULL_REPORT.keys()) > 0:
        NULL_FILE = os.path.join(COMPETITION_FOLDER, "null.json")
        with open(NULL_FILE, 'w') as outfile:
            outfile.write(json.dumps(NULL_REPORT, indent=4))


def rename():
    REPORT_FILE = os.path.join(COMPETITION_FOLDER, "report.json")
    JSON_REPORT = json.load(open(REPORT_FILE))

    # Get list of all files only in the given directory
    # Sort list of files based on last modification time in ascending order
    onlyFiles = filter(lambda x: os.path.isfile(os.path.join(COMPETITION_FOLDER, x)), os.listdir(COMPETITION_FOLDER))
    onlyFiles = sorted(onlyFiles, key=lambda x: os.path.getmtime(os.path.join(COMPETITION_FOLDER, x)))
    onlyFiles.remove("report.json")
    try:
        onlyFiles.remove("null.json")
    except Exception:
        print("No Null")
    counter = 0

    # Goto through every race
    for raceTitle in JSON_REPORT.keys():
        # Create race folders
        SESSION_FOLDER = os.path.join(COMPETITION_FOLDER, raceTitle)
        if not os.path.exists(SESSION_FOLDER):
            os.mkdir(SESSION_FOLDER)

        # Goto through every race session -> Rename files
        sessions = JSON_REPORT[raceTitle]
        for sessionTitle in sessions:
            src = os.path.join(COMPETITION_FOLDER, onlyFiles[counter])
            ext = "." + onlyFiles[counter].split(".")[-1]
            dst = os.path.join(os.path.join(COMPETITION_FOLDER, SESSION_FOLDER), sessionTitle) + ext
            os.rename(src, dst)
            counter += 1
            print(src)
            print(dst)
            print("")

    os.remove(REPORT_FILE)
    return


if __name__ == '__main__':
    print("------------------------------")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Set action
    ACTION = sys.argv[1]

    # Set URL
    URL = sys.argv[2]

    # Videos Folder / JDownloader
    SAVE_FOLDER = r"D:\SERIES"
    JDjarFile = r"C:\Users\xhico\AppData\Local\JDownloader 2.0\JDownloader.jar"

    try:
        # Launch burningwhee1s
        headless = True
        options = Options()
        options.headless = headless
        service = Service(r"C:\Users\xhico\OneDrive\Useful\geckodriver.exe")
        browser = webdriver.Firefox(service=service, options=options)

        browser.get(URL + "?max-results=100")

        # Create competition Folder
        competitionTitle = browser.title.replace("BurningWhee1s: ", "").replace(".", "")
        COMPETITION_FOLDER = os.path.join(SAVE_FOLDER, competitionTitle)
        if not os.path.exists(COMPETITION_FOLDER):
            os.mkdir(COMPETITION_FOLDER)

        # Check which action
        if ACTION == "download":
            # Remember to launch JDownloader first
            input("INFO: Open JDownloader (press key)")
            download()
        elif ACTION == "rename":
            rename()
    except Exception as ex:
        print(ex)
    finally:
        browser.close()
        print("End")
