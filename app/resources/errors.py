from cryptic import MicroserviceException

from app import wrapper
from models.wallet import Wallet
from schemes import unknown_source_or_destination, permission_denied


def wallet_exists(data: dict, user: str) -> Wallet:
    wallet: Wallet = wrapper.session.query(Wallet).get(data["source_uuid"])

    if wallet is None:
        raise MicroserviceException(unknown_source_or_destination)

    return wallet


def can_access_wallet(data: dict, user: str, wallet: Wallet) -> Wallet:
    if wallet.key != data["key"]:
        raise MicroserviceException(permission_denied)

    return wallet
