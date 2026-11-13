from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.modules.custom_fields import models as custom_fields_models  # noqa: E402,F401
from app.modules.jobs import models as jobs_models  # noqa: E402,F401
