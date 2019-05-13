import datetime
from typing import Union
from uuid import uuid4

from sqlalchemy import Column, Integer, String, DateTime, exists, and_

from app import wrapper


class Wallet(wrapper.Base):
    __tablename__: str = "wallet"

    time_stamp: Union[Column, datetime.datetime] = Column(DateTime, nullable=False)
    source_uuid: Union[Column, str] = Column(String(36), primary_key=True, unique=True)
    key: Union[Column, str] = Column(String(16))
    amount: Union[Column, int] = Column(Integer, nullable=False, default=0)
    user_uuid: Union[Column, str] = Column(String(36), unique=True)

    @property
    def serialize(self) -> dict:
        _: str = self.source_uuid
        d = self.__dict__

        del d['_sa_instance_state']

        return d

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
        wrapper.session.add(wallet)
        wrapper.session.commit()
        return {"success": "Your wallet has been created. ", "uuid": str(source_uuid), "key": str(key)}

    @staticmethod
    def auth_user(source_uuid: str, key: str) -> bool:
        return wrapper.session.query(
            wrapper.session.query(Wallet).filter(Wallet.source_uuid == source_uuid, Wallet.key == key).exists()).scalar()
