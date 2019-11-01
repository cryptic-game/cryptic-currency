from cryptic import MicroService, DatabaseWrapper

m: MicroService = MicroService("currency")

wrapper: DatabaseWrapper = m.get_wrapper()
