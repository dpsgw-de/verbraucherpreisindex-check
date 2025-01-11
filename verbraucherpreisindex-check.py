# Author: Fabian Lipp

import io
import smtplib
import zipfile
from email.mime.text import MIMEText

import pandas as pd
import requests
from dotenv import dotenv_values, load_dotenv

# Load credentials from .env file
load_dotenv()
USERNAME = dotenv_values()['USERNAME']
PASSWORD = dotenv_values()['PASSWORD']
CURRENT_VALUE_VERTRAG = dotenv_values()['CURRENT_VALUE_VERTRAG']
MINIMUM_FACTOR = dotenv_values()['MINIMUM_FACTOR']
MAIL_SENDER = dotenv_values()['MAIL_SENDER']
MAIL_RECIPIENTS = dotenv_values()['MAIL_RECIPIENTS']
MAIL_SUBJECT = dotenv_values()['MAIL_SUBJECT']

# Set base path for API calls
BASE_URL = 'https://www-genesis.destatis.de/genesisWS/rest/2020/'

response = requests.get(BASE_URL + 'data/tablefile', params={
    'username': USERNAME,
    'password': PASSWORD,
    'name': '61111-0002',
    'area': 'all',
    'compress': 'true',
    'format': 'ffcsv',
    'language': 'de'
})


zf = zipfile.ZipFile(io.BytesIO(response.content))
file = zf.open(zf.filelist[0].filename)

df = pd.read_csv(file, sep=";",
                 decimal=",", na_values=["-", "x", ".", "/"]) \
    .sort_values(by=["time", "value_variable_label"])
last_row = df.loc[
    df['value_variable_label'] == "Verbraucherpreisindex"].sort_values(
    by=["time", "1_variable_attribute_code"]).tail(1)
year = last_row['time'].values[0]
month = last_row['1_variable_attribute_label'].values[0]
value = last_row['value'].values[0]

result = (f"=== {MAIL_SUBJECT} ===\n"
          f"\n"
          f"Der Vebraucherpreisindex für {month} {year} ist {value}.\n"
          f"Der Vertrag basiert derzeit auf einem Index von {CURRENT_VALUE_VERTRAG}.\n"
          f"Das ist eine Erhöhung um {value / float(CURRENT_VALUE_VERTRAG) * 100 - 100} %. "
          f"Ab {MINIMUM_FACTOR} kann eine Erhöhung der Miete gefordert werden.")

print(result)

msg = MIMEText(result)
msg['Subject'] = MAIL_SUBJECT
msg['From'] = MAIL_SENDER
msg['To'] = MAIL_RECIPIENTS

s = smtplib.SMTP('localhost')
s.sendmail(MAIL_SENDER, MAIL_RECIPIENTS.split(","), msg.as_string())
s.quit()
