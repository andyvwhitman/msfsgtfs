from flask import Flask, Config
import os

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.urandom(24)

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}

app = Flask(__name__)
env = os.getenv('MSFSGTFS_ENV', 'development')
app.config.from_object(config_map[env])

print(app.config['DEBUG'])