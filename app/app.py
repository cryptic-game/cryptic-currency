from objects_init import engine, Base
from resources.handle import m


if __name__ == '__main__':
    
    Base.metadata.create_all(bind=engine)

    m.run()
