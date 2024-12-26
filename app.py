import os
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from pymongo import MongoClient
import requests

load_dotenv()

x_username = os.getenv("username")
x_pass = os.getenv("password")
webshare_proxy = os.getenv("WEBSHARE_PROXY")
mongo_uri = os.getenv("MONGO_URI")

app = Flask(__name__)

client = MongoClient(mongo_uri)
db = client['trending_topics']
collection = db['scrape_results']

def get_current_ip(proxy):
    try:
        response = requests.get(
            "https://ipv4.webshare.io/",
            proxies={
                "http": proxy,
                "https": proxy
            },
            timeout=10
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error getting IP: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_trending', methods=['GET'])
def get_trending():
    driver = Chrome()
    driver.maximize_window()

    final_topics = []
    scrape_id = str(uuid.uuid4())
    current_ip = get_current_ip(webshare_proxy)

    try:
        url = "https://x.com/i/flow/login"
        driver.get(url)

        username = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'input[autocomplete="username"]')
            )
        )
        username.send_keys(x_username)
        username.send_keys(Keys.ENTER)

        password = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
        )
        password.send_keys(x_pass)
        password.send_keys(Keys.ENTER)

        time.sleep(10)

        trending_box = driver.find_element(
            By.XPATH,
            ".//section[@aria-labelledby='accessible-list-1' or @aria-labelledby='accessible-list-2' or @aria-labelledby='accessible-list-3' or @aria-labelledby='accessible-list-4' or @aria-labelledby='accessible-list-5' or @aria-labelledby='accessible-list-6' or @aria-labelledby='accessible-list-7' or @aria-labelledby='accessible-list-8' or @aria-labelledby='accessible-list-9']",
        )

        topic_boxes = trending_box.find_elements(By.XPATH, '//div[@data-testid="trend"]')

        for topic in topic_boxes[:5]:
            trending_name = topic.find_element(By.XPATH, ".//div[contains(@style, 'color: rgb(231, 233, 234)')]//span").text
            final_topics.append(trending_name)

        scrape_data = {
            'scrape_id': scrape_id,
            'trend1': final_topics[0] if len(final_topics) > 0 else None,
            'trend2': final_topics[1] if len(final_topics) > 1 else None,
            'trend3': final_topics[2] if len(final_topics) > 2 else None,
            'trend4': final_topics[3] if len(final_topics) > 3 else None,
            'trend5': final_topics[4] if len(final_topics) > 4 else None,
            'timestamp': datetime.now(),
            'proxy_ip': current_ip,
            'proxy_used': webshare_proxy
        }

        collection.insert_one(scrape_data)

    except Exception as e:
        error_data = {
            'scrape_id': scrape_id,
            'timestamp': datetime.now(),
            'proxy_ip': current_ip,
            'proxy_used': webshare_proxy,
            'error': str(e)
        }
        collection.insert_one(error_data)
        return jsonify({"error": str(e)})

    finally:
        driver.quit()

    return jsonify({
        "scrape_id": scrape_id,
        "topics": final_topics,
        "timestamp": datetime.now().isoformat(),
        "proxy_ip": current_ip
    })

@app.route('/get_history', methods=['GET'])
def get_history():
    history = list(collection.find(
        {'trend1': {'$exists': True}},
        {'_id': 0}
    ).sort('timestamp', -1).limit(10))
    
    for item in history:
        item['timestamp'] = item['timestamp'].isoformat()
        if 'proxy_used' in item:
            del item['proxy_used']
    
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True)