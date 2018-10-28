from flask_sqlalchemy import SQLAlchemy
from flask_restplus import Api

db: SQLAlchemy = SQLAlchemy()
api: Api = Api(
    version='1.0',
    title="cryptic-currency",
    description="currency application programming interface of cryptic-game",
    authorizations={
        "token": {
            "type": "apiKey",
            "in": "header",
            "name": "Token"
        }
    }
)
