#test
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
import time
import os
import shutil
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


#pull yesterday
d1 = datetime.now()- timedelta(hours=24)
ts1 = d1.strftime("%m/%d/%Y")

d2 = datetime.now()
ts2 = d2.strftime("%m/%d/%Y")

options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

#initial login page
driver.get(config['beiweroot'])

driver.find_element("name", "username").send_keys(config['beiwename'])
driver.find_element("name", "password").send_keys(config['beiwepass'])
driver.find_element("name", "submit").submit()

#web access page
driver.get(config['beiweroot'] + '/data_access_web_form')

driver.find_element("name", "access_key").send_keys(config['accesskey'])
driver.find_element("name", "secret_key").send_keys(config['secretkey'])

select = Select(driver.find_element('name', 'study_pk'))
select.select_by_visible_text('Test_Study')

select = Select(driver.find_element('name', 'user_ids'))
select.select_by_value('wrsserra')

select = Select(driver.find_element('name', 'data_streams'))
for i in range(len(select.options)):
    select.select_by_index(i)

driver.find_element("name", "time_start").send_keys(ts1 + " 12:00 AM")
driver.find_element("name", "time_end").send_keys(ts2 + " 12:00 AM")
driver.find_element("id", "download_submit_button").submit()

#wait while downloads
time.sleep(30)

#get latest file in downloads and check it
path = '/Users/davidramsay/Downloads/'
os.chdir(path)
files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
newest = files[-1]

if ('data' in newest and '.zip' in newest):
    filename = d1.strftime("%m%d%y_beiwedata.zip")
    os.rename(newest, filename)
    shutil.copy(filename, '/Users/davidramsay/Desktop/twitch_stuff/TwitchTools/GrabAllData/beiwe/'+filename)
else:
    print('ERROR IDENTIFYING FILE')

