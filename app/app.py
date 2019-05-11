from objects import engine, Base
from cryptic import MicroService

m: MicroService = MicroService('currency')

if __name__ == '__main__':
    from resources.wallet import *

    Base.metadata.create_all(bind=engine)

    m.run()
