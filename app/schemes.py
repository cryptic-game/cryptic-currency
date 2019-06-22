from scheme import *

scheme_default: dict = {
    "source_uuid": UUID(),
    "key": Text(pattern=r'^[a-f0-9]{10}$'),
}

scheme_send: dict = {
    "source_uuid": UUID(),
    "key": Text(pattern=r'^[a-f0-9]{10}$'),
    "send_amount": Integer(minimum=1),
    "destination_uuid": UUID(),
    "usage": Text()
}

success_scheme: dict = {"ok": True}

permission_denied: dict = {"error": "permission_denied"}

already_own_a_wallet: dict = {"error": "already_own_a_wallet"}

source_or_destination_invalid: dict = {"error": "unknown_source_or_destination"}

you_make_debt: dict = {"error": "not_enough_coins"}
