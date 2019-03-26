from cryptic import MicroService
from resources.handle import handle, handle_ms

if __name__ == '__main__':
    m: MicroService = MicroService('wallet', handle, handle_ms)
    m.run()
