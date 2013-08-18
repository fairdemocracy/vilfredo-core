# default configuration settings

# WARNNG: must be changed in production!

# DATABASE_URI = 'sqlite:////var/tmp/vr.db'
development_db = 'sqlite:////var/tmp/vr.db'

# DATABASE_URI = development_db
SQLALCHEMY_DATABASE_URI = development_db

# WARNNG: must be changed to False in production!
DEBUG = True

# WARNNG: must be changed in production!
SECRET_KEY = 'ai4ohngaek4ohchaesheeY2Xee2jishe'

# mail server settings - ARNNG: must be changed to False in production!
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USERNAME = 'admin'
MAIL_PASSWORD = None
MAIL_SUPPRESS_SEND = True

# administrator list
ADMINS = ['admin@example.com']

# name of logger configuration file
LOG_CONFIG_FILE = 'logging_debug.conf'

# Probably don't need this
SITE_DOMAIN = 'localhost'

# Directory to put the voting maps - it will be created if not found
MAP_PATH = 'maps/'
