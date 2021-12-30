"""Copyright (C) 2021 SierraKiloBravo
This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; version 2.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA."""

from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By

class O365Authentication:
    def __init__(self, driver: webdriver.firefox.webdriver.WebDriver):
        assert isinstance(driver, webdriver.firefox.webdriver.WebDriver)
        self.driver = driver
        pass
    
    def _check_login_page(self):
        # Verify if the current page is a O365 login page before sending credentials there
        # A bit rudimentary, some additional checks are needed, probably.
        assert self.driver.title == "Sign In"
        assert self.driver.find_element(By.XPATH, '//*[@id="loginMessage"]').text == "Sign in with your organizational account"
        return True
    
    def login(self, username: str, password: str):
        self._check_login_page()
        # Log in using O365 credentials.
        # TODO: handle authentication errors (ie incorrect password)
        username_input = self.driver.find_element(By.XPATH, '//*[@id="userNameInput"]')
        password_input = self.driver.find_element(By.XPATH, '//*[@id="passwordInput"]')
        submit_button = self.driver.find_element(By.XPATH, '//*[@id="submitButton"]')
        username_input.send_keys(username)
        password_input.send_keys(password)
        
        submit_button.click()
