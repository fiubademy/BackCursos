from app.db import test_engine, Base
from app.api.courses import set_engine

Base.metadata.drop_all(test_engine)
Base.metadata.create_all(test_engine)
session = set_engine(test_engine)
