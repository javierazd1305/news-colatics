import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from pathlib import Path
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def postTwitter(text, username, password):
    CHROMEDRIVER_PATH = "/app/.chromedriver/bin/chromedriver"
    GOOGLE_CHROME_BIN = os.environ.get('GOOGLE_CHROME_BIN', '/usr/bin/google-chrome')
    #path = os.getcwd()+"/chromedriver"
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_bin = os.environ.get('GOOGLE_CHROME_BIN', "chromedriver")
    chrome_options.binary_location = chrome_bin
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
    #driver = webdriver.Chrome(executable_path=path, options=chrome_options)
    driver.get("https://twitter.com/login")
    username_field = driver.find_element_by_class_name("js-username-field")
    password_field = driver.find_element_by_class_name("js-password-field")
    username_field.send_keys(username)
    driver.implicitly_wait(1)
    password_field.send_keys(password)
    driver.implicitly_wait(1)
    driver.find_element_by_class_name("EdgeButtom--medium").click()
    autotw1 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[id='tweet-box-home-timeline']")))
    autotw1.send_keys(text)
    tweet = driver.find_element_by_xpath("//span[@class='add-tweet-button ']//following-sibling::button[contains(@class,'tweet-action')]")
    tweet.click()
    driver.close()
    print("twitter post finished")

def checkIfPost():
    today = time.strftime("%d-%m-%Y")
    SITE_ROOT = os.path.dirname(os.path.realpath('__file__'))
    file = SITE_ROOT + "/pubs/"+ today
    post = os.path.isdir(file)
    return (post, file)

def getText(path):
    with open(path+"/pub_text.txt", encoding='utf8') as f:
        text = f.read().strip()
    return text

def getTextDrive():
    SITE_ROOT = os.path.dirname(os.path.realpath('__file__'))
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SITE_ROOT + '/client_secret.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1DzRtMn2QYnelu264dzQw4lPPoKgUxpQ7wKwMqp7Ijos/edit#gid=0")
    sheet_ = sheet.worksheet("pub")
    data = sheet_.get_all_records()
    df_data = pd.DataFrame(data)
    today = time.strftime("%d/%m/%Y")
    df_post = pd.DataFrame()
    if df_data[df_data["date"].map(str) == today].shape[0] >0:
        df_post = df_data[df_data["date"].map(str) == today]
    return (df_post)

def updatePostStatus(index_row, index_col):
    SITE_ROOT = os.path.dirname(os.path.realpath('__file__'))
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SITE_ROOT + '/client_secret.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1DzRtMn2QYnelu264dzQw4lPPoKgUxpQ7wKwMqp7Ijos/edit#gid=0")
    sheet_ = sheet.worksheet("pub")
    sheet_.update_cell(index_row+2, index_col, 'ok')
def wrapper():
    username = "colatics.community@gmail.com"
    password = "weed4269"
    df_post = getTextDrive()
    print("get_df_post:", df_post.shape)
    if df_post.shape[0]>0:
        for index, row in df_post.iterrows():
            twitter = row["twitter"]
            facebook = row["facebook"]
            instagram = row["instagram"]
            text = row["text"]
            if twitter != "ok":
                print("twitter")
                #postTwitter(text, username, password)
                #updatePostStatus(index, 4)
wrapper()
