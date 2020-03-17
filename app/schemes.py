from scheme import Text, Integer, UUID

scheme_default: dict = {"source_uuid": UUID(), "key": Text(pattern=r"^[a-f0-9]{10}$")}

scheme_reset: dict = {"source_uuid": UUID()}

scheme_transactions: dict = {**scheme_default, "offset": Integer(minimum=0), "count": Integer(minimum=1)}

scheme_send: dict = {
    "source_uuid": UUID(),
    "key": Text(pattern=r"^[a-f0-9]{10}$"),
    "send_amount": Integer(minimum=1),
    "destination_uuid": UUID(),
    "usage": Text(),
}

success_scheme: dict = {"ok": True}

permission_denied: dict = {"error": "permission_denied"}

already_own_a_wallet: dict = {"error": "already_own_a_wallet"}

unknown_source_or_destination: dict = {"error": "unknown_source_or_destination"}

not_enough_coins: dict = {"error": "not_enough_coins"}
