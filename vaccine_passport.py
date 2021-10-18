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
import os

class Agent():
    def __init__(self):
        self.landing = 'https://covid19.ontariohealth.ca/'
        self.wait_s = 5  # adjust to latency, in seconds

        self.w_d = os.path.dirname(os.path.realpath(__file__))
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

            # wait
            print('Waiting for {0} seconds!'.format(this_wait))
            for second in range(this_wait, 0, -1):
                if second%30 == 0:
                    print('About {0} seconds left!'.format(second))
                time.sleep(1)


    def fill_info(self):
        '''
        Fill info, click continue

        No error checking due to time constraints
        '''
        pattern = re.compile('[\W_]+')

        # FILL INFO
        hcn = WebDriverWait(self.driver, self.wait_s).until(
            EC.presence_of_element_located((By.ID, "hcn"))
        )
        self.staggered_type(hcn, pattern.sub('', self.config['health_card_number'].lower()))  # fill health card number
        time.sleep(self.wait_s/5)  # buffer

        self.staggered_type(self.driver.find_element_by_id("vcode"), pattern.sub('', self.config['version_code'].lower()))  # fill version code
        time.sleep(self.wait_s/5)  # buffer

        self.staggered_type(self.driver.find_element_by_id("scn"), pattern.sub('', self.config['back_code'].lower()))  # fill code on back of card
        time.sleep(self.wait_s/5)  # buffer

        self.staggered_type(self.driver.find_element_by_id("dob"), pattern.sub('', self.config['dob'].lower()))  # fill date of birth
        time.sleep(self.wait_s/5)  # buffer

        self.staggered_type(self.driver.find_element_by_id("postal"), pattern.sub('', self.config['postal_code'].lower()))  # fill postal code
        time.sleep(self.wait_s/5)  # buffer

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
    

    def staggered_type(self, elm, input):
        '''
        elm as typeable selenium field element
        input as string input to type into elm
        '''
        for character in input:
            elm.send_keys(character)
            time.sleep(self.wait_s/10)



    def run(self):
        self.init_driver()
        while True:
            self.queue_up()
            self.wait_queue()
            self.fill_info()
            if not self.check_error():
                break
        
        print('Complete! You are now ready to obtain your vaccine passport.')
    

if __name__ == '__main__':
    agent = Agent()
    agent.run()