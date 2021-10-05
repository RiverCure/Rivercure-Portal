# from django.test import TestCase
# from django.contrib.staticfiles.testing import StaticLiveServerTestCase
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.webdriver import WebDriver

# class SeleniumTests(StaticLiveServerTestCase):

#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.selenium = WebDriver()
#         cls.selenium.implicitly_wait(10)

#     @classmethod
#     def tearDownClass(cls):
#         cls.selenium.quit()
#         super().tearDownClass()

#     def test_register(self):
#         self.selenium.get(f'{self.live_server_url}/register/')
#         username_input = self.selenium.find_element_by_name('username')
#         username_input.send_keys('testuser')
#         email_input = self.selenium.find_element_by_name('email')
#         email_input.send_keys('testuser')
#         # TODO: incomplete

#     def test_login(self):
#         # Arrange
#         self.selenium.get(f'{self.live_server_url}/login/')
#         username_input = self.selenium.find_element_by_name('username')
#         username_input.send_keys('admin')
#         password_input = self.selenium.find_element_by_name('password')
#         password_input.send_keys('admin')
#         # Act
#         print(self.selenium.find_element_by_xpath("//*[contains(text(), 'Log In')]"))
#         self.selenium.find_element_by_css_selector(".btn.btn-outline-info").click()
#         # Assert
#         self.selenium.find_element_by_xpath("//*[contains(text(), 'Log In')]")

