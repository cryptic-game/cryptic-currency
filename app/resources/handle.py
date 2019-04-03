from cryptic import MicroService

from models.transaction_db import Transaction
from models.wallet_db import Wallet
from objects_init import session
from schemes import *

m: MicroService = MicroService('wallet')


@m.user_endpoint(path=["create"])
def create(data: dict, user: str) -> dict:
    if 'user_uuid' not in data:
        return {"wallet_response": {"error": "Key 'user_uuid' has to be set for endpoint create."}}

    wallet_response: dict = Wallet.create(user)

    return wallet_response


@m.user_endpoint(path=["get"])
def get(data: dict, user: str) -> dict:
    if 'source_uuid' not in data:
        return source_uuid_missing
    if 'key' not in data:
        return key_missing

    if not Wallet.auth_user(data["source_uuid"], data["key"]):
        return invalid_key

    amount: int = session.query(Wallet).get(data["source_uuid"]).amount

    return {"success": {"amount": amount, "transactions": Transaction.get(data["source_uuid"])}}


@m.user_endpoint(path=["send"])
def send(data: dict, user: str) -> dict:
    if 'source_uuid' not in data:
        return source_uuid_missing
    if 'key' not in data:
        return key_missing
    if 'send_amount' not in data:
        return send_amount_missing
    if 'destination_uuid' not in data:
        return destination_missing
    if 'usage' not in data:
        usage: str = ''
    else:
        usage: str = data['usage']

    if Wallet.auth_user(data["source_uuid"], data["key"]) is False:
        return invalid_key

    source_wallet: Wallet = session.query(Wallet).filter_by(uuid=data["source_uuid"]).first()
    destination_wallet: Wallet = session.query(Wallet).filter_by(uuid=data["destination_uuid"]).first()

    if source_wallet is None or destination_wallet is None:
        return source_or_destination_invalid

    if source_wallet.amount - data["amount"] < 0 or data["amount"] < 0:
        return you_make_debt

    source_wallet.amount -= data["amount"]
    destination_wallet.amount += data["amount"]
    session.commit()

    Transaction.create(data["source_uuid"], data["amount"], data["destination_uuid"], usage)

    return {"ok": True}


@m.user_endpoint(path=["delete"])
def delete(data: dict, user: str) -> dict:
    if 'source_uuid' not in data:
        return source_uuid_missing
    source_uuid: str = data['source_uuid']
    wallet: Wallet = session.query(Wallet).filter_by(uuid=source_uuid).first()
    if wallet is None:
        return source_or_destination_invalid

    session.delete(wallet)

    session.commit()

    return {"ok": True}