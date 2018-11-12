from flask_restplus import Namespace, Resource, fields, abort
from basics import ErrorSchema, require_session
from objects import api, db
from flask import request
from models.wallet import WalletModel
from functools import wraps
from typing import Optional

WalletCreateTransferRequestSchema = api.model("Wallet Create Transfer Request", {
    "recipient": fields.String(example="12abc34d5efg67hi89j1klm2nop3pqrs",
                               description="recipient of the 'money'",
                               required=True),
    "amount": fields.Integer(example="1234",
                             desription="the mount of 'money' the recipient will receive",
                             required=True)
})

WalletResponseSchema = api.model("Wallet Response", {
    "uuid": fields.String(example="12abc34d5efg67hi89j1klm2nop3pqrs",
                          description="the wallets's public uuid"),
    "key": fields.String(example="12abc34d5efg67hi89j1klm2nop3pqrs12abc34d5efg67hi89j1klm2nop3pqrs",
                         description="the wallets's key"),
    "amount": fields.String(example="1234",
                            description="the wallets's value")
})


def require_wallet(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'Key' in request.headers:
            key: str = request.headers["Key"]

            if len(key) != 64:
                abort(400, "invalid formatted key")

            kwargs["key"] = key

            return f(*args, **kwargs)
        else:
            abort(400, "key required")

    return wrapper


def get_wallet(uuid, key) -> Optional[WalletModel]:
    """
    Tries to get the wallet by the wallets uuid and key
    :param uuid: the wallet's uuid
    :param key: the wallet's key
    :return: maybe the WalletModel
    """
    wallet: Optional[WalletModel] = WalletModel.query.filter_by(uuid=uuid).first()

    if wallet is None:
        abort(404, "invalid wallet uuid")

    if wallet.key != key:
        abort(403, "no access to this wallet")

    return wallet


wallet_api = Namespace('wallet')


@wallet_api.route('')
@wallet_api.doc("Wallet Application Programming Interface")
class WalletAPI(Resource):

    @wallet_api.doc("Create a wallet", security="token")
    @wallet_api.marshal_with(WalletResponseSchema)
    @wallet_api.response(400, "Invalid Input", ErrorSchema)
    @require_session
    def put(self, session):
        return WalletModel.create().serialize


@wallet_api.route('/<string:uuid>')
@wallet_api.doc("Wallet Modification Application Programming Interface")
class WalletModificationAPI(Resource):

    @wallet_api.doc("Get data about the wallet", security="token")
    @wallet_api.marshal_with(WalletResponseSchema)
    @wallet_api.response(400, "Invalid Input", ErrorSchema)
    @wallet_api.response(403, "No Access", ErrorSchema)
    @wallet_api.response(404, "Not Found", ErrorSchema)
    @require_session
    @require_wallet
    def get(self, session, key, uuid):
        wallet: Optional[WalletModel] = get_wallet(uuid, key)
        return wallet.serialize

    @wallet_api.doc("Send money to someone", security="token")
    @wallet_api.marshal_with(WalletResponseSchema)
    @wallet_api.expect(WalletCreateTransferRequestSchema, validate=True)
    @wallet_api.response(400, "Invalid Input", ErrorSchema)
    @wallet_api.response(403, "No Access", ErrorSchema)
    @wallet_api.response(404, "Not Found", ErrorSchema)
    @require_session
    @require_wallet
    def post(self, session, key, uuid):
        wallet: Optional[WalletModel] = get_wallet(uuid, key)
        amount: int = request.json["amount"]

        if amount < 0:
            abort(400, "invalid amount to send")
        elif amount > wallet.amount:
            abort(400, "not enough money")

        recipient: str = request.json["recipient"]

        if len(recipient) != 32:
            abort(400, "invalid recipient uuid")

        recipient: Optional[WalletModel] = WalletModel.query.filter_by(uuid=recipient).first()

        if recipient is None:
            abort(404, "unknown recipient uuid")

        recipient.amount += amount
        wallet.amount -= amount
        db.session.commit()

        return wallet.serialize
