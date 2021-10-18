from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import json
import re
import time

class Agent():
    def __init__(self):
        self.landing = 'https://covid19.ontariohealth.ca/'
        self.wait_s = 5  # adjust to latency, in seconds

        with open('{0}/config.json'.format(self.w_d)) as f:
            self.config = json.load(f)
    

    def init_driver(self):
        try:
            self.driver = webdriver.Chrome()
        except:
            # automatically install chromedriver
            self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.driver.maximize_window()
        print('Driver started!')
    

    def queue_up(self):
        '''
        Driver needs to be initiated
        '''
        self.driver.get(self.landing)  # navigate to landing page
        WebDriverWait(self.driver, self.wait_s).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".fal.fa-square.fa-stack-1x"))
        ).click()  # accept terms
        self.driver.find_element_by_id('continue_button').click()  # place in queue
        print('Queued up!')


    def wait_queue(self):
        '''
        '''
        estimated = None

        while True:
            # get time remaining
            try:
                # get estimated wait time
                estimated = WebDriverWait(self.driver, self.wait_s).until(
                    EC.presence_of_element_located((By.ID, "MainPart_lbWhichIsIn"))
                ).text
            except TimeoutException:
                # estimated wait time not on page, wait over
                print('Queue complete!')
                return
            
            # extract time remaining
            this_wait = [int(s) for s in estimated.split() if s.isdigit()]
            if this_wait:
                this_wait = this_wait[0] * 60 + 60  # convert to seconds, add a minute buffer
            else:
                this_wait = 60  # less than a minute remaining, wait for a minute

            time.sleep(this_wait)  # wait


    def fill_info(self):
        '''
        Fill info, click continue

        No error checking due to time constraints
        '''
        pattern = re.compile('[\W_]+')

        # FILL INFO
        # fill health card number
        WebDriverWait(self.driver, self.wait_s).until(
            EC.presence_of_element_located((By.ID, "hcn"))
        ).send_keys(pattern.sub('', self.config['health_card_number'].lower()))
        self.driver.find_element_by_id("vcode").send_keys(pattern.sub('', self.config['version_code'].lower()))  # fill version code
        self.driver.find_element_by_id("scn").send_keys(pattern.sub('', self.config['back_code'].lower()))  # fill code on back of card
        self.driver.find_element_by_id("dob").send_keys(pattern.sub('', self.config['dob'].lower()))  # fill date of birth
        self.driver.find_element_by_id("postal").send_keys(pattern.sub('', self.config['postal_code'].lower()))  # fill postal code

        self.driver.find_element_by_id("continue_button").click()  # continue
        print('Info filled!')

    def check_error(self):
        '''
        Check for 'our services aren't available right now' error page
        '''
        try:
            message = WebDriverWait(self.driver, self.wait_s).until(
                EC.presence_of_element_located((By.ID, 'message'))
            ).text.lower()  # look for error message
            if "aren't available" in message:
                raise TimeoutException  # found error message, raise anyway
            print('Error page, restarting process!\n')
            return True
        except TimeoutException:
            return False
    
    def run(self):

        while True:
            self.init_driver()
            self.queue_up()
            self.wait_queue()
            self.fill_info()
            if not self.check_error():
                break
        
        print('Complete! You are now ready to obtain your vaccine passport.')
    

if __name__ == '__main__':
    agent = Agent()
    agent.run()