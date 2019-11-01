from cryptic import MicroService, Config, DatabaseWrapper

m: MicroService = MicroService("currency")

wrapper: DatabaseWrapper = m.get_wrapper()
