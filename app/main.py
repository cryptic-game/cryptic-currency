import app


if __name__ == "__main__":
    from resources.wallet import *

    app.wrapper.Base.metadata.create_all(bind=wrapper.engine)

    app.m.run()
