import os
import time
from threading import Thread
from wsgiref.simple_server import make_server

import yaml

from lettuce import after
from lettuce import before
from lettuce import world
from selenium import webdriver

import lettuce_webdriver.webdriver

from velruse.app import make_app

config_dir = os.path.dirname(os.path.dirname(__file__))
config_file = os.path.join(config_dir, 'config.yaml')
login_page = os.path.join(config_dir, 'html_pages', 'signup_page.html')

class VelruseServer(Thread):
    def __init__(self, config_file):
        Thread.__init__(self)
        app = make_app(config_file)
        self.httpd = make_server('', 9090, app)
        self.keep_running = True
    
    def run(self):
        while self.keep_running:
            try:
                self.httpd.handle_request()
            except Exception, e:
                pass
            time.sleep(0.2)
    
    def kill(self):
        self.keep_running = False

@before.all
def setup_app():
    f = open(config_file, 'r')
    content = f.read()
    f.close()
    config = yaml.load(content)
    
    if 'Facebook Credentials' in config:
        fb_config = config['Facebook Credentials']
        world.facebook_email = fb_config['Username'].strip()
        world.facebook_password = fb_config['Password'].strip()
    
    world.login_page = 'file://%s' % login_page
    world.browser = webdriver.Firefox()
    
    # Setup the velruse app thread
    world.velruse_thread = VelruseServer(config_file)
    world.velruse_thread.start()

@after.all
def teardown(total):
    while world.velruse_thread.isAlive():
        world.velruse_thread.kill()
        world.browser.get(world.login_page)
        world.velruse_thread.join(1)
    world.browser.quit()
