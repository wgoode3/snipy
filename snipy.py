#!/usr/bin/python3
## encoding:utf-8--

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
import json, time

START_URL = "https://signin.ebay.com/ws/eBayISAPI.dll?SignIn"
BASE_URL = "https://www.ebay.com/itm/{}"


class Snipy:

    def __init__(self):
        self.settings = {}
        with open("settings.json") as file:
            self.settings = json.loads(file.read())
        self.driver = webdriver.Firefox()
        self.driver.set_page_load_timeout(self.settings["page_load_timeout"])

    def get_url(self, url, retries=None):
        if retries == None:
            retries = self.settings["page_load_retries"]
        if retries < 0:
            raise Exception("too many failed attempts at connecting to: {}".format(url))
        try:
            self.driver.get(url)
            return
        except TimeoutException:
            print("retrying", retries)
            self.get_url(url, retries-1)

    def get_end_datetime(self):
        time_elements = self.driver.find_elements_by_class_name("timeMs")
        if(len(time_elements) > 0):
            end_timestamp = time_elements[0].get_attribute("timems")
            return int(end_timestamp)//1000
        else:
            raise Exception("Time not found")

    def extract_price_from_text(self, text, currency="$"):
        p = ""
        i = text.find(currency) + 1
        while text[i] != " ":
            p += text[i]
            i += 1
        return p

    def login_to_ebay(self):
        self.driver.find_element_by_id("userid").send_keys(self.settings["email"])
        self.driver.find_element_by_id("pass").send_keys(self.settings["password"])
        self.driver.find_element_by_id("sgnBt").click()

    def bid_on_item(self):
        amt = -1
        bid_note = self.driver.find_elements_by_class_name("bid-note")
        if(len(bid_note) > 0):
            amt = self.extract_price_from_text(bid_note[0].text)
        if amt != -1 and float(amt) <= self.settings["max_bid"]:
            self.driver.find_element_by_id("MaxBidId").send_keys(str(self.settings["max_bid"]))
            self.driver.find_element_by_id("bidBtn_btn").click()
            time.sleep(5)
            self.driver.find_element_by_id("confirm_button").click()
            return True
        return False

    def run(self):
        self.get_url(BASE_URL.format(self.settings["item_id"]))
        endtime = self.get_end_datetime()
        time_to_end = endtime - int(time.time())
        time_to_bid = time_to_end - self.settings["time_before_bid"]
        print("bidding in {} seconds".format(time_to_bid))
        time.sleep(time_to_bid)
        self.get_url(START_URL)
        self.login_to_ebay()
        self.get_url(BASE_URL.format(self.settings["item_id"]))
        if self.bid_on_item():
            print("Success!!!")
        else:
            print("Failure...")
        time.sleep(2)
        self.driver.quit()

if __name__ == "__main__":
    sniper = Snipy()
    sniper.run()