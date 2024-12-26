import os
import random
import time
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

load_dotenv()

x_username = os.getenv("username")
x_pass = os.getenv("password")
proxies = os.getenv("PROXIES").split(",")
chrome_dpath = os.getenv("CHROME_DRIVER_PATH")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_trending', methods=['GET'])
def get_trending():
    proxy = random.choice(proxies)
    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_argument(f"--proxy-server={proxy}")

    driver = webdriver.Chrome(options=options)

    final_topics = []

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

        for topic in topic_boxes:
            trending_name = topic.find_element(By.XPATH, ".//div[contains(@style, 'color: rgb(231, 233, 234)')]//span").text
            final_topics.append(trending_name)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        driver.quit()

    return jsonify({"topics": final_topics})

if __name__ == '__main__':
    app.run(debug=True)
