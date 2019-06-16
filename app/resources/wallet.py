from sqlalchemy import func

from app import m, wrapper
from models.transaction import Transaction
from models.wallet import Wallet
from schemes import *


@m.user_endpoint(path=["create"], requires={})
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


@m.user_endpoint(path=["get"], requires=scheme_default)
def get(data: dict, user: str) -> dict:
    if not Wallet.auth_user(data["source_uuid"], data["key"]):
        return permission_denied

    amount: int = wrapper.session.query(Wallet).get(data["source_uuid"]).amount

    return {"success": {"amount": amount, "transactions": Transaction.get(data["source_uuid"])}}


@m.user_endpoint(path=["send"], requires=scheme_send)
def send(data: dict, user: str) -> dict:
    usage: str = data['usage']

    if Wallet.auth_user(data["source_uuid"], data["key"]) is False:
        return permission_denied

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


@m.user_endpoint(path=["delete"], requires=scheme_default)
def delete(data: dict, user: str) -> dict:
    source_uuid: str = data['source_uuid']
    key: str = data['key']
    wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=source_uuid, key=key).first()
    if wallet is None:
        return source_or_destination_invalid

    wrapper.session.delete(wallet)
    wrapper.session.commit()

    return {"ok": True}


@m.microservice_endpoint(path=["exists"])
def exists(data: dict, microservice: str) -> dict:
    return {"exists": wrapper.session.query(Wallet).filter_by(source_uuid=data["source_uuid"]).first() is not None}


@m.microservice_endpoint(path=["put"])
def put(data: dict, microservice: str) -> dict:
    source_uuid: str = data["source_uuid"]
    amount: int = data["amount"]
    destination_uuid: str = data["destination_uuid"]
    usage: str = data["usage"]

    wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=destination_uuid).first()
    if wallet is None:
        return source_or_destination_invalid

    wallet.amount += amount
    wrapper.session.commit()

    transaction: Transaction = Transaction.create(source_uuid, amount, destination_uuid, usage)

    return transaction.serialize


@m.microservice_endpoint(path=["dump"])
def dump(data: dict, microservice: str) -> dict:
    source_uuid: str = data["source_uuid"]
    key: str = data["key"]
    amount: int = data["amount"]
    destination_uuid: str = data["destination_uuid"]
    usage: str = data["usage"]

    wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=source_uuid).first()
    if wallet is None:
        return source_or_destination_invalid
    if wallet.key != key:
        return permission_denied

    if wallet.amount < amount:
        return you_make_debt
    wallet.amount -= amount
    wrapper.session.commit()

    transaction: Transaction = Transaction.create(source_uuid, amount, destination_uuid, usage)

    return transaction.serialize
