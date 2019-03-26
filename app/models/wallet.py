from uuid import uuid4
import objects_init as db
from sqlalchemy import Column, Integer, String, DateTime, exists, and_, or_
import datetime


class Transaction(db.base):
    __tablename__: str = "transaction"

    id: Column = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    time_stamp: Column = Column(DateTime, nullable=False)
    source_uuid: Column = Column(String(36))
    send_amount: Column = Column(Integer, nullable=False, default=0)
    destination_uuid: Column = Column(String(36))
    usage: Column = Column(String, default='')

    @property
    def serialize(self) -> dict:
        _ = self.id
        return {**self.__dict__}

    @staticmethod
    def create(source_uuid: str, send_amount: int, destination_uuid: str, usage: str):
        # create transaction and add it to database
        """
        Returns a transaction of a source_uuid.
        :return: transactions
        """
        # Create a new TransactionModel instance
        transaction: Transaction = Transaction(
            time_stamp=datetime.datetime.now(),
            source_uuid=source_uuid,
            send_amount=send_amount,
            destination_uuid=destination_uuid,
            usage=usage
        )

        # Add the new transaction to the db
        db.session.add(transaction)
        db.session.commit()

    @staticmethod
    def get(source_uuid):
        transactions: list = []
        for i in db.session.query(Transaction).filter(or_(Transaction.source_uuid == source_uuid,
                                                          Transaction.destination_uuid == source_uuid)):
            transactions.append({"time_stamp": str(i.time_stamp), "source_uuid": str(i.source_uuid),
                                 "amount": int(i.send_amount), "destination_uuid": str(i.destination_uuid),
                                 "usage": str(i.usage)})
        return transactions


class Wallet(db.base):
    __tablename__: str = "wallet"

    time_stamp: Column = Column(DateTime, nullable=False)
    source_uuid: Column = Column(String(36), primary_key=True, unique=True)
    key: Column = Column(String(16))
    amount: Column = Column(Integer, nullable=False, default=0)
    user_uuid: Column = Column(String(36), unique=True)

    # auf objekt serialize anwenden und dann kriege ich aus objekt ein dict zurueck
    @property
    def serialize(self) -> dict:
        _ = self.source_uuid
        return {**self.__dict__}

    @staticmethod
    def create(user_uuid: str) -> dict:
        """
        Creates a new wallet.
        :return: dict with status
        """
        # empty user uuid
        if user_uuid == "":
            return {"error": "You have to paste the user uuid to create a wallet."}

        source_uuid: str = str(uuid4())
        # uuid is 32 chars long -> now key is 10 chars long
        key: str = str(uuid4()).replace("-", "")[:10]

        # Create a new Wallet instance
        wallet: Wallet = Wallet(
            time_stamp=datetime.datetime.now(),
            source_uuid=source_uuid,
            key=key,
            amount=100,
            user_uuid=user_uuid
        )

        # Add the new wallet to the db
        db.session.add(wallet)
        db.session.commit()
        return {"success": "Your wallet has been created. ", "uuid": str(source_uuid), "key": str(key)}

    # for checking the amount of morph coins and transactions
    @staticmethod
    def get(source_uuid: str, key: str) -> dict:
        if source_uuid == "" or key == "":
            return {"error": "Source UUID or Key is empty."}
        # no valid key -> no status of balance
        if not Wallet.auth_user(source_uuid, key):
            return {"error": "Your UUID or wallet key is wrong or you have to create a wallet."}
        amount: int = db.session.query(Wallet).get(source_uuid).amount
        # transactions = db.session.query(Wallet)
        return {"success": {"amount": amount, "transactions": Transaction.get(source_uuid)}}

    @staticmethod
    def send_coins(source_uuid: str, key: str, send_amount: int, destination_uuid: str, usage: str = "") -> dict:
        if source_uuid == "" or key == "":
            return {"error": "Source UUID or Key is empty."}
        # if no random key was generated and the key is still not activated the user will not send coins
        if not Wallet.auth_user(source_uuid, key):
            return {"error": "Your UUID or wallet key is wrong or "
                             "you have to create a wallet before sending morph coins!"}
        if destination_uuid == "":
            return {"error": "Destination UUID is empty."}
        if not db.session.query(exists().where(Wallet.source_uuid == destination_uuid)).scalar():
            return {"error": "Destination does not exist."}
        if send_amount <= 0:
            return {"error": "You can only send more than 0 morph coins."}
        # if the wanted amount to send is higher than the current balance it will fail to transfer
        if send_amount > db.session.query(Wallet).filter(Wallet.source_uuid == source_uuid).first().amount:
            return {"error": "Transfer failed! You have not enough morph coins."}
        # Update in Database
        source_uuid_amount = db.session.query(Wallet).get(source_uuid).amount
        destination_uuid_amount = db.session.query(Wallet).get(destination_uuid).amount
        db.session.query(Wallet).filter(Wallet.source_uuid == source_uuid)\
            .update({'amount': source_uuid_amount - send_amount})
        db.session.commit()
        db.session.query(Wallet).filter(Wallet.source_uuid == destination_uuid)\
            .update({'amount': destination_uuid_amount + send_amount})
        db.session.commit()
        # insert transaction into table db transactions
        transaction = Transaction()
        transaction.create(source_uuid, send_amount, destination_uuid, usage)
        # successful status mail with transfer information
        return {"success": "Transfer of " + str(send_amount) + " morph coins from " + str(source_uuid) +
                           " to " + str(destination_uuid) + " successful!"}

    @staticmethod
    def auth_user(source_uuid: str, key: str) -> bool:
        return db.session.query(exists().where(and_(Wallet.source_uuid == source_uuid, Wallet.key == key))).scalar()

    # resets password in database if user forget it
    @staticmethod
    def reset(source_uuid: str) -> dict:
        if source_uuid == "":
            return {"error": "Source UUID is empty."}
        if not db.session.query(exists().where(Wallet.source_uuid == source_uuid)).scalar():
            return {"error": "Source UUID does not exist."}
        key: str = str(uuid4())[:10]
        db.session.query(Wallet).filter(Wallet.source_uuid == source_uuid).update({'key': key})
        db.session.commit()
        return {"success": "Your wallet key has been updated.", "uuid": str(source_uuid), "key": str(key)}

    @staticmethod
    def gift(send_amount: int, destination_uuid: str) -> dict:
        if send_amount <= 0:
            return {"error": "You can only send an absolute amount. 0 is not included."}
        amount = db.session.query(Wallet).filter(Wallet.source_uuid == destination_uuid).first().amount
        db.session.query(Wallet).filter(Wallet.source_uuid == destination_uuid).update({'amount': amount + send_amount})
        return {"success": "Gift of " + str(send_amount) + " to " + str(destination_uuid) + " successful!"}

    @staticmethod
    def delete(source_uuid: str) -> dict:
        if not db.session.query(exists().where(Wallet.source_uuid == source_uuid)).scalar():
            return {"error": "Source UUID does not exist."}
        db.session.query(Wallet).filter(Wallet.source_uuid == source_uuid).delete(synchronize_session=False)
        db.session.commit()
        return {"success": "Deletion of " + str(source_uuid) + " successful."}

    @staticmethod
    def delete_all_wallets():
        db.session.query(Wallet).delete()
        db.session.commit()

    @staticmethod
    def print_all_wallets():
        print("–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––")
        print("--------------------------------------WALLET-DATABASE--------------------------------------------------")
        print("------------------------------------------CRYPTIC------------------------------------------------------")
        print("-------------------------------------------------------------------------------------------------------")
        print("--------source_uuid--------------|-wallet_key-|-------------user_id--------------|--------amount-------")
        print("–––––––––––––––––––––––––––––––––|––––––––––––|––––––––––––––––––––––––––––––––––––––––––––––––––––––––")
        for user_wallet in db.session.query(Wallet).all():
            print(user_wallet.source_uuid, user_wallet.key, user_wallet.user_uuid, user_wallet.amount, sep=' | ')


db.base.metadata.create_all(bind=db.engine)
