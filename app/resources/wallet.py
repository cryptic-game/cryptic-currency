from cryptic import MicroService
from models.wallet import Wallet, db


def handle(endpoint: list, data: dict) -> dict:
    """
    The handle method to get data from server to know what to do
    :param endpoint: the action of the server 'get', 'create', 'send'
    :param data: source_uuid, key, send_amount, destination_uuid ...
    :return: wallet response for actions
    """
    # test the casting
    try:
        str(data['user_uuid'])
        str(data['source_uuid'])
        str(data['key'])
        int(data['send_amount'])
        str(data['destination_uuid'])
        str(data['usage'])
    except ValueError:
        return {"wallet_response": "Your input data is in a wrong format!", "user_uuid": "str", "source_uuid": "str",
                "key": "str", "send_amount": "int", "destination_uuid": "str",
                "usage": "str"}
    except KeyError:
        pass
    # every time the handle method is called, a new wallet object is created
    # wallet: Wallet = Wallet()
    db.base.metadata.create_all(bind=db.engine)
    # endpoint[0] will be the action what to do in an array ['get', ...]
    if endpoint[0] == 'create':
        try:
            user_uuid: str = data['user_uuid']
        except KeyError:
            return {"wallet_response": "Key 'user_uuid' have to be set for endpoint create."}
        wallet_response: dict = Wallet.create(user_uuid)
    elif endpoint[0] == 'get':
        try:
            source_uuid: str = data['source_uuid']
            key: str = data['key']
        except KeyError:
            return {"wallet_response": "Keys 'source_uuid' and 'key' have to be set for endpoint get."}
        wallet_response: dict = Wallet.get(source_uuid, key)
    elif endpoint[0] == 'send':
        try:
            usage: str = data['usage']
        except KeyError:
            usage: str = ''
        try:
            source_uuid: str = data['source_uuid']
            key: str = data['key']
            send_amount: int = data['send_amount']
            destination_uuid: str = data['destination_uuid']
        except KeyError:
            return {"wallet_response": "Keys 'source_uuid' and 'key' and 'send_amount' "
                                       "and 'destination_uuid' have to be set for endpoint send."
                                       "You can also use key 'usage' for specify your transfer."}
        wallet_response: dict = Wallet.send_coins(source_uuid, key, send_amount, destination_uuid, usage)
    elif endpoint[0] == 'reset':
        try:
            source_uuid: str = data['source_uuid']
        except KeyError:
            return {"wallet_response": "Key 'source_uuid' has to be set for the endpoint reset."}
        wallet_response: dict = Wallet.reset(source_uuid)
    elif endpoint[0] == 'gift':
        try:
            send_amount: int = data['send_amount']
            source_uuid: str = data['source_uuid']
        except KeyError:
            return {"wallet_response": "Keys 'source_uuid' and 'send_amount' have to be set for endpoint gift."}
        wallet_response: dict = Wallet.gift(send_amount, source_uuid)
    elif endpoint[0] == 'delete':
        try:
            source_uuid: str = data['source_uuid']
        except KeyError:
            return {"wallet_response": "Key 'source_uuid' has to be set for endpoint delete."}
        wallet_response: dict = Wallet.delete(source_uuid)
    else:
        wallet_response: dict = {"error": "Endpoint is not supported."}
    return {"wallet_response": wallet_response}


def handle_ms(ms, data, tag):
    print(ms, data, tag)


if __name__ == '__main__':
    m = MicroService('wallet', handle, handle_ms)
    m.run()
