from cryptic import MicroService, Config, DatabaseWrapper, get_config

config: Config = get_config("debug")  # / production

m: MicroService = MicroService('currency')

wrapper: DatabaseWrapper = m.get_wrapper()

if __name__ == '__main__':
    from resources.handle import *

    wrapper.Base.metadata.create_all(bind=wrapper.engine)

    m.run()
