from sqlalchemy import Column, Integer, Sequence
from sqlalchemy.sql.sqltypes import String

from wps_shared.db.models import Base


class FireCentre(Base):
    """BC Wildfire Service Fire Centre."""

    __tablename__ = "fire_centres"

    id = Column(
        Integer, Sequence("fire_centres_id_seq"), primary_key=True, nullable=False, index=True
    )
    name = Column(String, nullable=False, index=True)

    def __str__(self):
        return f"id:{self.id}, name:{self.name}"
