from typing import Optional

from app import m, wrapper
from models.transaction import Transaction
from models.wallet import Wallet
from schemes import *


def update_miner(wallet: Wallet):
    wallet.amount += m.contact_microservice("service", ["miner", "collect"], {"wallet_uuid": wallet.source_uuid})[
        "coins"
    ]
    wrapper.session.commit()


@m.user_endpoint(path=["create"], requires={})
def create(data: dict, user: str) -> dict:
    wallet: Optional[Wallet] = wrapper.session.query(Wallet).filter_by(user_uuid=user).first()
    if wallet is not None:
        return already_own_a_wallet

    wallet: Wallet = Wallet.create(user)

    return wallet.serialize


@m.user_endpoint(path=["get"], requires=scheme_default)
def get(data: dict, user: str) -> dict:
    source_uuid: str = data["source_uuid"]
    wallet: Wallet = wrapper.session.query(Wallet).get(source_uuid)
    if wallet is None:
        return unknown_source_or_destination
    if wallet.key != data["key"]:
        return permission_denied

    update_miner(wallet)

    return {**wallet.serialize, "transactions": Transaction.get(source_uuid)}


@m.user_endpoint(path=["list"], requires={})
def list_wallets(data: dict, user: str) -> dict:
    return {"wallets": [wallet.source_uuid for wallet in wrapper.session.query(Wallet).filter_by(user_uuid=user)]}


@m.user_endpoint(path=["send"], requires=scheme_send)
def send(data: dict, user: str) -> dict:
    usage: str = data["usage"]

    if Wallet.auth_user(data["source_uuid"], data["key"]) is False:
        return permission_denied

    source_wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=data["source_uuid"]).first()
    destination_wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=data["destination_uuid"]).first()

    if source_wallet is None or destination_wallet is None:
        return unknown_source_or_destination

    update_miner(source_wallet)

    if source_wallet.amount - data["send_amount"] < 0 or data["send_amount"] < 0:
        return not_enough_coins

    source_wallet.amount -= data["send_amount"]
    destination_wallet.amount += data["send_amount"]
    wrapper.session.commit()

    Transaction.create(data["source_uuid"], data["send_amount"], data["destination_uuid"], usage, origin=0)

    return success_scheme


@m.user_endpoint(path=["reset"], requires=scheme_reset)
def reset(data: dict, user: str) -> dict:
    source_uuid: str = data["source_uuid"]

    wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=source_uuid).first()
    if wallet is None:
        return unknown_source_or_destination

    if wallet.user_uuid != user:
        return permission_denied

    wrapper.session.delete(wallet)
    wrapper.session.commit()

    return success_scheme


@m.user_endpoint(path=["delete"], requires=scheme_default)
def delete(data: dict, user: str) -> dict:
    source_uuid: str = data["source_uuid"]
    key: str = data["key"]
    wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=source_uuid, key=key).first()
    if wallet is None:
        return unknown_source_or_destination

    wrapper.session.delete(wallet)
    wrapper.session.commit()

    return success_scheme


@m.microservice_endpoint(path=["exists"])
def exists(data: dict, microservice: str) -> dict:
    return {"exists": wrapper.session.query(Wallet).filter_by(source_uuid=data["source_uuid"]).first() is not None}


@m.microservice_endpoint(path=["put"])
def put(data: dict, microservice: str) -> dict:
    amount: int = data["amount"]
    destination_uuid: str = data["destination_uuid"]

    wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=destination_uuid).first()
    if wallet is None:
        return unknown_source_or_destination

    wallet.amount += amount
    wrapper.session.commit()

    if not data["create_transaction"]:
        return success_scheme

    source_uuid: str = data["source_uuid"]
    usage: str = data["usage"]
    origin: int = data["origin"]

    transaction: Transaction = Transaction.create(source_uuid, amount, destination_uuid, usage, origin)
    return transaction.serialize


@m.microservice_endpoint(path=["dump"])
def dump(data: dict, microservice: str) -> dict:
    source_uuid: str = data["source_uuid"]
    key: str = data["key"]
    amount: int = data["amount"]

    wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=source_uuid).first()
    if wallet is None:
        return unknown_source_or_destination
    if wallet.key != key:
        return permission_denied

    update_miner(wallet)

    if wallet.amount < amount:
        return not_enough_coins
    wallet.amount -= amount
    wrapper.session.commit()

    if not data["create_transaction"]:
        return success_scheme

    destination_uuid: str = data["destination_uuid"]
    usage: str = data["usage"]
    origin: int = data["origin"]

    transaction: Transaction = Transaction.create(source_uuid, amount, destination_uuid, usage, origin)
    return transaction.serialize


@m.microservice_endpoint(path=["delete_user"])
def delete_user(data: dict, microservice: str) -> dict:
    user: str = data["user_uuid"]

    wrapper.session.query(Wallet).filter_by(user_uuid=user).delete()
    wrapper.session.commit()

    return success_scheme
