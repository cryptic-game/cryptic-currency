from objects import db
from uuid import uuid4


class WalletModel(db.Model):
    __tablename__: str = "wallet"

    uuid: db.Column = db.Column(db.String(32), primary_key=True, unique=True)
    key: db.Column = db.Column(db.String(64), unique=True)
    amount: db.Column = db.Column(db.Integer, nullable=False, default=0)

    @property
    def serialize(self) -> dict:
        _ = self.uuid
        return {**self.__dict__}

    @staticmethod
    def create() -> 'WalletModel':
        """
        Creates a new wallet.
        :return: New wallet
        """

        uuid: str = str(uuid4()).replace("-", "")
        key: str = str(uuid4()).replace("-", "") + str(uuid4()).replace("-", "")

        # Create a new Wallet instance
        wallet: WalletModel = WalletModel(
            uuid=uuid,
            key=key,
            amount=0
        )

        # Add the new wallet to the db
        db.session.add(wallet)
        db.session.commit()

        return wallet
