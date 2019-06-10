import urllib3
from bs4 import BeautifulSoup
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import os
import progressbar
from get_abstract import textRankAlgorithm, getParagraph
from requests_html import HTMLSession
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from twitter_post import getTextDrive, postTwitter, updatePostStatus
def get_soup_forbes():
    CHROMEDRIVER_PATH = "/app/.chromedriver/bin/chromedriver"
    GOOGLE_CHROME_BIN = os.environ.get('GOOGLE_CHROME_BIN', '/usr/bin/google-chrome')

    forbes_url_init = "https://www.forbes.com/"
    topic = "ai-big-data"
    url = forbes_url_init + topic

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_bin = os.environ.get('GOOGLE_CHROME_BIN', "chromedriver")
    chrome_options.binary_location = chrome_bin
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    path = os.getcwd()+"/chromedriver"
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
    driver.get(url)
    time.sleep(5)
    htmlSource = driver.page_source
    return htmlSource

def get_df_forbes(soup):
    soup = BeautifulSoup(soup, 'html.parser')
    df = pd.DataFrame(columns = ["date","type","title","url","abstract"])
    session = HTMLSession()
    a_tags = soup.findAll('a')
    regex_date = re.compile(r'\d\d\d\d/\d\d/\d\d')
    topic = "ai-big-data"
    for i in progressbar.progressbar(a_tags):
        h2_tags = i.find('h2')
        if h2_tags is not None:
            title = h2_tags.text.replace("\t","").replace("\n","")
            url_new = i.get('href')
            html_new = session.get(url_new)
            soup_new = BeautifulSoup(html_new.html.html, 'html.parser')
            text_new = soup_new.findAll('p')
            paragraph = ""
            for i in text_new:
                paragraph += i.text
            abstract = textRankAlgorithm(paragraph)
            date = ""
            date = regex_date.search(url_new).group(0)
            type = "Article - " + topic
            df = df.append({'date':date, 'type': type, 'title':title, 'url': url_new, 'abstract':abstract}, ignore_index=True)
    return df

def get_new_forbes():
    soup_forbes = get_soup_forbes()
    df_forbes = get_df_forbes(soup_forbes)
    return df_forbes

def get_new_mckinsey():
    mckinsey_url_init = "https://www.mckinsey.com"
    mckinsey_types = ["Article", "Interview", "Commentary","DiscussionPaper"]
    url = "https://www.mckinsey.com/business-functions/mckinsey-analytics/our-insights"
    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET',url)
    soup = BeautifulSoup(r.data.decode('utf-8'), 'html.parser')
    items = soup.findAll('div', attrs={'class':"item"})
    df = pd.DataFrame(columns = ["date","type","title","url","abstract"])
    for i in progressbar.progressbar(items):
        new = i.find('span', attrs={'class':'eyebrow'})
        new_type = new.text.replace("\t","").replace("\n","").replace(" ","").split("-")[0]
        if new_type in mckinsey_types:
            text_wrapper = i.find('div', attrs={'class':'text-wrapper'})
            date = text_wrapper.find('div', attrs={'class':'description'})
            date_text = date.find('time').text.replace("\t","").replace("\n","")
            title = text_wrapper.find('a')
            title_text = title.text.replace("\t","").replace("\n","")
            url = mckinsey_url_init + title.get('href')
            paragraph = getParagraph(url)
            abstract = textRankAlgorithm(paragraph)
            df = df.append({'date':date_text, 'type': new_type, 'title':title_text, 'url': url, 'abstract':abstract}, ignore_index=True)
    return df

def get_new_hbr():
    hbr_url_init = "https://hbr.org/"
    url = "https://hbr.org/topic/data"
    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET',url)
    soup = BeautifulSoup(r.data.decode('utf-8'), 'html.parser')
    items = soup.findAll('div', attrs={'class':'row'})
    df = pd.DataFrame(columns = ["date","type","title","url","abstract"])
    for i in progressbar.progressbar(items):
        try:
            title = i.find('h3', attrs={'class': 'hed'})
            url =  hbr_url_init + title.find('a').get("href")
            title_text =title.text.replace("\t","").replace("\n","")
            type = i.find('span', attrs={'class':'content-type'})
            type_text = type.text.replace("\t","").replace("\n","")
            date_ul = i.find('ul', attrs={'class':'stream-utility plain-inline-list'})
            date_li = date_ul.find('li', attrs={'class':'utility pubdate'})
            date_text = date_li.text.replace("\t","").replace("\n","")
            paragraph = getParagraph(url)
            abstract = textRankAlgorithm(paragraph)
            df = df.append({'date':date_text, 'type': type_text, 'title':title_text, 'url': url, 'abstract':abstract}, ignore_index=True)
        except:
            pass
    return df

def send_data(sheet_name, df):
    SITE_ROOT = os.path.dirname(os.path.realpath('__file__'))
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SITE_ROOT + '/client_secret.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1k-ersaEgGhnAXU3Xah715J8BKdZtrJHdOdwMuwqFgzQ/edit#gid=0")
    sheet_ = sheet.worksheet(sheet_name)
    data = sheet_.get_all_records()
    df_diff = get_new_entries(sheet_name, df)
    for index, i in df_diff.iterrows():
        sheet_.append_row([len(data)+1+index, i["date"], i["type"], i["title"], i["url"], i["abstract"]])

def get_new_entries(sheet_name, df):
    SITE_ROOT = os.path.dirname(os.path.realpath('__file__'))
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SITE_ROOT + '/client_secret.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1k-ersaEgGhnAXU3Xah715J8BKdZtrJHdOdwMuwqFgzQ/edit#gid=0")
    sheet_ = sheet.worksheet(sheet_name)
    data = sheet_.get_all_records()
    df_data = pd.DataFrame(data)
    if df_data.shape[0] == 0:
        return df
    else:
        df_data.drop("id", axis=1, inplace=True)
        set_diff_df = pd.concat([df, df_data, df_data], sort=False).drop_duplicates(keep=False)
        set_diff_df.reset_index(inplace=True)
        return set_diff_df

def McKinsey():
    print("Init McKinsey:")
    df_mckinsey = get_new_mckinsey()
    send_data("McKinsey", df_mckinsey)
    print("finished McKinsey")
def HBR():
    print("Init HBR:")
    df_hbr = get_new_hbr()
    send_data("HBR", df_hbr)
    print("finished HBR")
def Forbes():
    print("Init Forbes:")
    df_forbes = get_new_forbes()
    send_data("Forbes", df_forbes)
    print("finished Forbes")


sched = BlockingScheduler()

@sched.scheduled_job('cron', day_of_week='sun', hour=17)
def init():
    McKinsey()
    HBR()
    Forbes()
@sched.scheduled_job('cron', day_of_week='mon-wed-fri-sun', hour=17)
def wrapper():
    username = "colatics.community@gmail.com"
    password = "weed4269"
    df_post = getTextDrive()
    if df_post.shape[0]>0:
        for index, row in df_post.iterrows():
            twitter = row["twitter"]
            facebook = row["facebook"]
            instagram = row["instagram"]
            text = row["text"]
            if twitter != "ok":
                print("twitter")
                postTwitter(text, username, password)
                updatePostStatus(index, 4)
            if instagram != "ok":
                pass
                # print("instagram")
                # updatePostStatus(index, 5)
            if facebook != "ok":
                pass
                # print("facebok")
                # updatePostStatus(index, 6)

sched.start()
