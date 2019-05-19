from app import m, wrapper
from models.transaction import Transaction
from models.wallet import Wallet
from schemes import *
from sqlalchemy import func


@m.user_endpoint(path=["create"])
def create(data: dict, user: str) -> dict:
    wallet_count: int = \
        (wrapper.session.query(func.count(Wallet.user_uuid)).filter(Wallet.user_uuid == user)).first()[0]

    if wallet_count < 1:
        wallet_response: dict = Wallet.create(user)

        return wallet_response
    else:
        return {
            "error": "You already own a wallet!"
        }


@m.user_endpoint(path=["get"])
def get(data: dict, user: str) -> dict:
    if 'source_uuid' not in data:
        return source_uuid_missing
    if 'key' not in data:
        return key_missing

    if not Wallet.auth_user(data["source_uuid"], data["key"]):
        return invalid_key

    amount: int = wrapper.session.query(Wallet).get(data["source_uuid"]).amount

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

    source_wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=data["source_uuid"]).first()
    destination_wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=data["destination_uuid"]).first()

    if source_wallet is None or destination_wallet is None:
        return source_or_destination_invalid

    if source_wallet.amount - data["send_amount"] < 0 or data["send_amount"] < 0:
        return you_make_debt

    source_wallet.amount -= data["send_amount"]
    destination_wallet.amount += data["send_amount"]
    wrapper.session.commit()

    Transaction.create(data["source_uuid"], data["send_amount"], data["destination_uuid"], usage)

    return {"ok": True}


@m.user_endpoint(path=["delete"])
def delete(data: dict, user: str) -> dict:
    if 'source_uuid' not in data:
        return source_uuid_missing
    if 'key' not in data:
        return key_missing

    source_uuid: str = data['source_uuid']
    key: str = data['key']
    wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=source_uuid, key=key).first()
    if wallet is None:
        return source_or_destination_invalid

    wrapper.session.delete(wallet)
    wrapper.session.commit()

    return {"ok": True}
