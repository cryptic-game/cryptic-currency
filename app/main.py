import app


# noinspection PyUnresolvedReferences
def load_endpoints():
    import resources.wallet


if __name__ == "__main__":
    load_endpoints()
    app.m.run()
