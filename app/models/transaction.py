import datetime
from typing import Union

from sqlalchemy import Column, Integer, String, DateTime, or_

from app import wrapper


class Transaction(wrapper.Base):
    __tablename__: str = "transaction"

    id: Union[Column, int] = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    time_stamp: Union[Column, datetime.datetime] = Column(DateTime, nullable=False)
    source_uuid: Union[Column, str] = Column(String(36))
    send_amount: Union[Column, int] = Column(Integer, nullable=False, default=0)
    destination_uuid: Union[Column, str] = Column(String(36))
    usage: Union[Column, str] = Column(String(255), default='')

    @property
    def serialize(self) -> dict:
        _: int = self.id
        d = self.__dict__

        del d['_sa_instance_state']

        return self.__dict__

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
        wrapper.session.add(transaction)
        wrapper.session.commit()

    @staticmethod
    def get(source_uuid):
        transactions: list = []
        for i in wrapper.session.query(Transaction).filter(or_(Transaction.source_uuid == source_uuid,
                                                               Transaction.destination_uuid == source_uuid)):
            transactions.append({"time_stamp": str(i.time_stamp), "source_uuid": str(i.source_uuid),
                                 "amount": int(i.send_amount), "destination_uuid": str(i.destination_uuid),
                                 "usage": str(i.usage)})
        return transactions
