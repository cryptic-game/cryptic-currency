import datetime
from typing import Union, List

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
        d = self.__dict__.copy()

        del d['_sa_instance_state']
        d["time_stamp"] = str(d["time_stamp"])

        return d

    @staticmethod
    def create(source_uuid: str, send_amount: int, destination_uuid: str, usage: str) -> 'Transaction':
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

        return transaction

    @staticmethod
    def get(source_uuid: str) -> List[dict]:
        return [
            transaction.serialize for transaction in
            wrapper.session.query(Transaction).filter(or_(Transaction.source_uuid == source_uuid,
                                                          Transaction.destination_uuid == source_uuid))
        ]
