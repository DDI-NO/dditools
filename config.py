import configparser

class ConfigManager:
    _instance = None

    def __new__(cls, config_file='config.ini'):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            # Initialize configuration here
            cls._instance.config = configparser.ConfigParser()
            cls._instance.config.read(config_file)
        return cls._instance

    def get(self, section, option):
        return self.config.get(section, option)

# Create an instance of the singleton
config_manager = ConfigManager()
