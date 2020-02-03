from typing import Optional

from cryptic import register_errors

from app import m, wrapper
from models.transaction import Transaction
from models.wallet import Wallet
from resources.errors import wallet_exists, can_access_wallet
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
@register_errors(wallet_exists, can_access_wallet)
def get(data: dict, user: str, wallet: Wallet) -> dict:
    update_miner(wallet)

    return {**wallet.serialize, "transactions": Transaction.get(wallet.source_uuid)}


@m.user_endpoint(path=["list"], requires={})
def list_wallets(data: dict, user: str) -> dict:
    return {"wallets": [wallet.source_uuid for wallet in wrapper.session.query(Wallet).filter_by(user_uuid=user)]}


@m.user_endpoint(path=["send"], requires=scheme_send)
@register_errors(wallet_exists, can_access_wallet)
def send(data: dict, user: str, source_wallet: Wallet) -> dict:
    destination_uuid: str = data["destination_uuid"]
    destination_wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=destination_uuid).first()

    if destination_wallet is None:
        return unknown_source_or_destination

    update_miner(source_wallet)

    amount: int = data["send_amount"]
    if source_wallet.amount - amount < 0 or amount < 0:
        return not_enough_coins

    source_wallet.amount -= amount
    destination_wallet.amount += amount
    wrapper.session.commit()

    Transaction.create(source_wallet.source_uuid, amount, destination_uuid, data["usage"], origin=0)

    m.contact_user(
        source_wallet.user_uuid,
        {
            "notify-id": "outgoing-transaction",
            "origin": "send",
            "wallet_uuid": source_wallet.source_uuid,
            "new_amount": source_wallet.amount,
        },
    )
    m.contact_user(
        destination_wallet.user_uuid,
        {
            "notify-id": "incoming-transaction",
            "origin": "send",
            "wallet_uuid": destination_wallet.source_uuid,
            "new_amount": destination_wallet.amount,
        },
    )

    return success_scheme


@m.user_endpoint(path=["reset"], requires=scheme_reset)
@register_errors(wallet_exists)
def reset(data: dict, user: str, wallet: Wallet) -> dict:
    if wallet.user_uuid != user:
        return permission_denied

    m.contact_microservice("service", ["miner", "stop"], {"wallet_uuid": wallet.source_uuid})

    wrapper.session.delete(wallet)
    wrapper.session.commit()

    return success_scheme


@m.user_endpoint(path=["delete"], requires=scheme_default)
@register_errors(wallet_exists, can_access_wallet)
def delete(data: dict, user: str, wallet: Wallet) -> dict:
    m.contact_microservice("service", ["miner", "stop"], {"wallet_uuid": wallet.source_uuid})

    wrapper.session.delete(wallet)
    wrapper.session.commit()

    return success_scheme


@m.microservice_endpoint(path=["exists"])
def exists(data: dict, microservice: str) -> dict:
    return {"exists": wrapper.session.query(Wallet).filter_by(source_uuid=data["source_uuid"]).first() is not None}


@m.microservice_endpoint(path=["owner"])
def owner(data: dict, microservice: str) -> dict:
    wallet: Optional[Wallet] = wrapper.session.query(Wallet).filter_by(source_uuid=data["source_uuid"]).first()
    if wallet is None:
        return unknown_source_or_destination

    return {"owner": wallet.user_uuid}


@m.microservice_endpoint(path=["put"])
def put(data: dict, microservice: str) -> dict:
    amount: int = data["amount"]
    destination_uuid: str = data["destination_uuid"]

    wallet: Wallet = wrapper.session.query(Wallet).filter_by(source_uuid=destination_uuid).first()
    if wallet is None:
        return unknown_source_or_destination

    wallet.amount += amount
    wrapper.session.commit()

    m.contact_user(
        wallet.user_uuid,
        {
            "notify-id": "incoming-transaction",
            "origin": "put",
            "wallet_uuid": wallet.source_uuid,
            "new_amount": wallet.amount,
        },
    )

    if not data["create_transaction"]:
        return success_scheme

    source_uuid: str = data["source_uuid"]
    usage: str = data["usage"]
    origin: int = data["origin"]

    transaction: Transaction = Transaction.create(source_uuid, amount, destination_uuid, usage, origin)
    return transaction.serialize


@m.microservice_endpoint(path=["dump"])
@register_errors(wallet_exists, can_access_wallet)
def dump(data: dict, microservice: str, wallet: Wallet) -> dict:
    amount: int = data["amount"]

    update_miner(wallet)

    if wallet.amount < amount:
        return not_enough_coins
    wallet.amount -= amount
    wrapper.session.commit()

    m.contact_user(
        wallet.user_uuid,
        {
            "notify-id": "outgoing-transaction",
            "origin": "dump",
            "wallet_uuid": wallet.source_uuid,
            "new_amount": wallet.amount,
        },
    )

    if not data["create_transaction"]:
        return success_scheme

    destination_uuid: str = data["destination_uuid"]
    usage: str = data["usage"]
    origin: int = data["origin"]

    transaction: Transaction = Transaction.create(wallet.source_uuid, amount, destination_uuid, usage, origin)
    return transaction.serialize


@m.microservice_endpoint(path=["delete_user"])
def delete_user(data: dict, microservice: str) -> dict:
    user: str = data["user_uuid"]

    wrapper.session.query(Wallet).filter_by(user_uuid=user).delete()
    wrapper.session.commit()

    return success_scheme
