from cryptic import MicroService, Config, DatabaseWrapper, get_config

config: Config = get_config()  # / production

m: MicroService = MicroService("currency")

wrapper: DatabaseWrapper = m.get_wrapper()
