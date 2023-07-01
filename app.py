from flask import Flask, request
from boltiot import Bolt
from twilio.rest import Client
from requests import get
import requests
import json
import threading
import time

# Bolt IoT credentials
bolt_api_key = "XXXXXXXX"
device_id = "XXXXXXXX"
bolt = Bolt(bolt_api_key, device_id)

# Twilio credentials
twilio_sid = "XXXXXXXX"
twilio_auth_token = "XXXXXXXX"
twilio_phone_number = "XXXXXXXX"
recipient_phone_number = "XXXXXXXX"

# Mailgun credentials
mailgun_api_key = "XXXXXXXX"
mailgun_domain = "XXXXXXXX"
mailgun_sender_email = "XXXXXXXX"
mailgun_recipient_email = "XXXXXXXX"

# Telegram bot credentials
telegram_token = "XXXXXXXX"
telegram_chat_id = "XXXXXXXX"

alpha_vantage_api_key = "XXXXXXXX"

print('Credentials done')

app = Flask(__name__)

stckSym = None  # Initialize the variable
price = None


@app.route('/', methods=['GET'])
def index():
    with open('index.html', 'r') as file:
        return file.read()


@app.route('/process_form', methods=['POST'])
def process_form():
    global stckSym, price
    stckSym = request.form.get('StkSym')
    price = request.form.get('ThrPrice')

    # Print the submitted values
    print("Stock Symbol:", stckSym)
    print("Threshold Price:", price)

    return "Form Submitted Successfully"


def trigger_alert():
    bolt.digitalWrite('1', 'HIGH')  # Activate the buzzer


def reset_alert():
    bolt.digitalWrite('1', 'LOW')  # Deactivate the buzzer

# Function to send SMS notification


def send_sms(message):
    client = Client(twilio_sid, twilio_auth_token)
    client.messages.create(
        body=message, from_=twilio_phone_number, to=recipient_phone_number)
    print('Sms done')

# Function to send email notification


def send_email(subject, message):
    print('email done')
    return requests.post(f"https://api.mailgun.net/v3/{mailgun_domain}/messages", auth=("api", mailgun_api_key), data={"from": mailgun_sender_email, "to": mailgun_recipient_email, "subject": subject, "text": message})

# Function to send Telegram message


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={telegram_chat_id}&text={message}"
    get(url)
    print('telegram done')

# Function to get stock price using Alpha Vantage API


def get_stock_price(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stckSym}&apikey=XXXXXXXX"
    response = requests.get(url)
    data = json.loads(response.text)

    if "Global Quote" in data:
        global_quote = data["Global Quote"]
        stock_price = float(global_quote.get(
            "05. price", global_quote.get("05. price", 0.0)))
        return stock_price
    print('getStockPrice done')

# Function to check stock price and trigger notifications


def check_stock_price():
    while True:
        global stckSym, price
        if stckSym is not None and price is not None:
            stock_price = get_stock_price(stckSym)
            print(stock_price)
            if stock_price is not None and stock_price >= float(price):
                print('in if')
                send_sms(
                    f"{stckSym} reached the threshold price of {price}")
                print('sms sent')
                send_email(f"{stckSym} reached the threshold price",
                           f"The current price is {stock_price}")
                print('email sent')
                send_telegram_message(
                    f"{stckSym} reached the threshold price of {price}")
                print('tele sent')
                trigger_alert()
                print('buzzer ON')
                print('if end')
            else:
                print('in else')
                print(stock_price)
                global cnt
                cnt = cnt + 1
                print(cnt)
                reset_alert()
                print('buzzer OFF')
                print('else end')
        print('checkStockPrice done')
        time.sleep(60)


threading.Thread(target=check_stock_price).start()

if __name__ == '__main__':
    app.run(debug=True)
