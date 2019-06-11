from scheme import *

scheme_default : dict = {
    "source_uuid": UUID(min_length=36, max_length=36),
    "key": Text(min_length=16, max_length=16),
}

scheme_send: dict = {
    "source_uuid": UUID(min_length=36, max_length=36),
    "key": Text(min_length=16, max_length=16),
    "send_amount": Integer(minimum=1),
    "destination_uuid": UUID(min_length=36, max_length=36),
    "usage": Text(optional=True)
}

permission_denied : dict = {"error": "permission_denied"}

source_or_destination_invalid: dict = {"error": "unknown_source_or_destination"}

you_make_debt: dict = {"error": "not_enough_coins"}
