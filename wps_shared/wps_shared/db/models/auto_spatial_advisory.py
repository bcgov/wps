import enum

from geoalchemy2 import Geometry
from sqlalchemy import (
    Column,
    Date,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import postgresql

from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.db.models.hfi_calc import FireCentre
from wps_shared.geospatial.geospatial import NAD83_BC_ALBERS


class HfiClassificationThresholdEnum(enum.Enum):
    """Enum for the different HFI classification thresholds."""

    ADVISORY = "advisory"
    WARNING = "warning"


class ShapeTypeEnum(enum.Enum):
    """Define different shape types. e.g. "Zone", "Fire Centre" - later we may add
    "Incident"/"Fire", "Custom" etc. etc."""

    fire_centre = 1
    fire_zone = 2
    fire_zone_unit = 3


class RunTypeEnum(enum.Enum):
    """Define different run types. e.g. "Forecast", "Actual" """

    forecast = "forecast"
    actual = "actual"


class TPIClassEnum(enum.Enum):
    valley_bottom = 1
    mid_slope = 2
    upper_slope = 3


class ShapeType(Base):
    """Identify some kind of area type, e.g. "Zone", or "Fire" """

    __tablename__ = "advisory_shape_types"
    __table_args__ = {"comment": "Identify kind of advisory area (e.g. Zone, Fire etc.)"}

    id = Column(Integer, primary_key=True)
    name = Column(Enum(ShapeTypeEnum), nullable=False, unique=True, index=True)


class Shape(Base):
    """Identify some area of interest with respect to advisories."""

    __tablename__ = "advisory_shapes"
    __table_args__ = (
        # we may have to re-visit this constraint - but for the time being, the idea is
        # that for any given type of area, it has to be unique for the kind of thing that
        # it is. e.g. a zone has some id.
        UniqueConstraint("source_identifier", "shape_type"),
        {"comment": "Record identifying some area of interest with respect to advisories"},
    )

    id = Column(Integer, primary_key=True)
    # An area is uniquely identified, e.g. a zone has a number, so does a fire.
    source_identifier = Column(String, nullable=False, index=True)
    shape_type = Column(Integer, ForeignKey(ShapeType.id), nullable=False, index=True)
    # The area in square meters of the shape's geom that has combustible fuels in it,
    # according to the fuel type layer
    # Have to make this column nullable to start because the table already exists. Will be
    # modified in subsequent migration to nullable=False
    combustible_area = Column(Float, nullable=True)
    geom = Column(
        Geometry("MULTIPOLYGON", spatial_index=False, srid=NAD83_BC_ALBERS), nullable=False
    )
    label = Column(String, nullable=True, index=False)
    placename_label = Column(String, nullable=True, index=False)
    fire_centre = Column(Integer, ForeignKey(FireCentre.id), nullable=True, index=True)


# Explicit creation of index due to issue with alembic + geoalchemy.
Index("idx_advisory_shapes_geom", Shape.geom, postgresql_using="gist")


class HfiClassificationThreshold(Base):
    __tablename__ = "advisory_hfi_classification_threshold"
    __table_args__ = {
        "comment": "The Operational Safe Works Standards specifies that an hfi of greater than "
        "4000 should result in an advisory. However in order for an FBAN to create "
        "useful information, there are other thresholds of concern. E.g. > 10000"
    }
    id = Column(Integer, primary_key=True, index=True)
    # e.g. '4000 < hfi < 10000' or 'hfi >= 10000'
    description = Column(String, nullable=False)
    # e.g. 'advisory' 'warning'
    name = Column(String, nullable=False)


class ClassifiedHfi(Base):
    """HFI classified into different groups.
    NOTE: In actual fact, forecasts and actuals can be run multiple times per day,
    but we only care about the most recent one, so we only store the date, not the timestamp.
    """

    __tablename__ = "advisory_classified_hfi"
    __table_args__ = {
        "comment": "HFI classification for some forecast/advisory run on some day, for some date"
    }
    id = Column(Integer, primary_key=True, index=True)
    threshold = Column(
        Integer, ForeignKey(HfiClassificationThreshold.id), nullable=False, index=True
    )
    run_type = Column(Enum(RunTypeEnum), nullable=False, index=True)
    run_datetime = Column(TZTimeStamp, nullable=False)
    for_date = Column(Date, nullable=False)
    geom = Column(Geometry("POLYGON", spatial_index=False, srid=NAD83_BC_ALBERS))


# Explicit creation of index due to issue with alembic + geoalchemy.
Index("idx_advisory_classified_hfi_geom", ClassifiedHfi.geom, postgresql_using="gist")


class FuelType(Base):
    """Identify some kind of fuel type."""

    __tablename__ = "advisory_fuel_types"
    __table_args__ = {"comment": "Identify some kind of fuel type"}
    id = Column(Integer, primary_key=True, index=True)
    fuel_type_id = Column(Integer, nullable=False, index=True)
    geom = Column(Geometry("POLYGON", spatial_index=False, srid=NAD83_BC_ALBERS))
    fuel_type_raster_id = Column(Integer, ForeignKey(FuelTypeRaster.id), nullable=True, index=True)


# Explicit creation of index due to issue with alembic + geoalchemy.
Index("idx_advisory_fuel_types_geom", FuelType.geom, postgresql_using="gist")


class SFMSFuelType(Base):
    """Fuel types used by SFMS system"""

    __tablename__ = "sfms_fuel_types"
    __table_args__ = {"comment": "Fuel types used by SFMS to calculate HFI spatially"}
    id = Column(Integer, primary_key=True, index=True)
    fuel_type_id = Column(Integer, nullable=False, index=True)
    fuel_type_code = Column(String, nullable=False)
    description = Column(String)


class RunParameters(Base):
    """Combination of type of run (actual vs forecast), run datetime and for date."""

    __tablename__ = "run_parameters"
    __table_args__ = (
        UniqueConstraint("run_type", "run_datetime", "for_date"),
        {"comment": "A combination of run type, run datetime and for date."},
    )
    id = Column(Integer, primary_key=True, index=True)
    run_type = Column(
        postgresql.ENUM("actual", "forecast", name="runtypeenum", create_type=False),
        nullable=False,
        index=True,
    )
    run_datetime = Column(TZTimeStamp, nullable=False, index=True)
    for_date = Column(Date, nullable=False, index=True)


class HighHfiArea(Base):
    """Area exceeding HFI thresholds per fire zone."""

    __tablename__ = "high_hfi_area"
    __table_args__ = {
        "comment": "Area under advisory/warning per fire zone. advisory_area refers to the total area "
        "in a fire zone with HFI values between 4000 - 10000 and warn_area refers to the total "
        "area in a fire zone with HFI values exceeding 10000."
    }

    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False)
    threshold = Column(Integer, ForeignKey(HfiClassificationThreshold.id), nullable=False)
    run_parameters = Column(Integer, ForeignKey(RunParameters.id), nullable=False, index=True)
    area = Column(Float, nullable=False)


class AdvisoryElevationStats(Base):
    """
    Summary statistics about the elevation of area with high hfi (4k-10k and >10k) per fire shape
    based on the set run_type, for_date and run_datetime.
    """

    __tablename__ = "advisory_elevation_stats"
    __table_args__ = {"comment": "Elevation stats per fire shape by advisory threshold"}
    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False, index=True)
    threshold = Column(Integer, ForeignKey(HfiClassificationThreshold.id), nullable=False)
    run_parameters = Column(Integer, ForeignKey(RunParameters.id), nullable=False, index=True)
    minimum = Column(Float, nullable=False)
    quartile_25 = Column(Float, nullable=False)
    median = Column(Float, nullable=False)
    quartile_75 = Column(Float, nullable=False)
    maximum = Column(Float, nullable=False)


class AdvisoryFuelStats(Base):
    """
    Summary statistics about the fuel type of area with high hfi (4k-10k and >10k) per fire shape
    based on the set run_type, for_date and run_datetime.
    """

    __tablename__ = "advisory_fuel_stats"
    __table_args__ = (
        UniqueConstraint("advisory_shape_id", "threshold", "run_parameters", "fuel_type"),
        {"comment": "Fuel type stats per fire shape by advisory threshold"},
    )
    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False, index=True)
    threshold = Column(Integer, ForeignKey(HfiClassificationThreshold.id), nullable=False)
    run_parameters = Column(Integer, ForeignKey(RunParameters.id), nullable=False, index=True)
    fuel_type = Column(Integer, ForeignKey(SFMSFuelType.id), nullable=False, index=True)
    area = Column(Float, nullable=False)
    fuel_type_raster_id = Column(Integer, ForeignKey(FuelTypeRaster.id), nullable=True, index=True)


class AdvisoryTPIStats(Base):
    """
    Summary statistics about the elevation based on a HFI >4k classified Topographic Position Index (TPI).
    Classification of the TPI are bucketed into 1 = valley bottom, 2 = mid slope, 3 = upper slope.
    Each record includes the raster pixel count of the above classifications as well as the raster pixel size and resolution in metres
    and an advisory shape the stats are related to.
    """

    __tablename__ = "advisory_tpi_stats"
    __table_args__ = {"comment": "Elevation TPI stats per fire shape"}
    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False, index=True)
    run_parameters = Column(Integer, ForeignKey(RunParameters.id), nullable=False, index=True)
    valley_bottom = Column(Integer, nullable=False, index=False)
    mid_slope = Column(Integer, nullable=False, index=False)
    upper_slope = Column(Integer, nullable=False, index=False)
    pixel_size_metres = Column(Integer, nullable=False, index=False)


class CriticalHours(Base):
    """
    Critical hours for a fuel type in a firezone unit.
    """

    __tablename__ = "critical_hours"
    __table_args__ = {
        "comment": "Critical hours by firezone unit, fuel type and sfms run parameters."
    }
    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False, index=True)
    threshold = Column(
        postgresql.ENUM(
            "advisory", "warning", name="hficlassificationthresholdenum", create_type=False
        ),
        nullable=False,
    )
    run_parameters = Column(Integer, ForeignKey(RunParameters.id), nullable=False, index=True)
    fuel_type = Column(Integer, ForeignKey(SFMSFuelType.id), nullable=False, index=True)
    start_hour = Column(Integer, nullable=False)
    end_hour = Column(Integer, nullable=False)
    fuel_type_raster_id = Column(Integer, ForeignKey(FuelTypeRaster.id), nullable=True, index=True)


class TPIFuelArea(Base):
    """
    Combustible area in each TPI class per fire zone unit.
    """

    __tablename__ = "tpi_fuel_area"
    __table_args__ = {"comment": "Combustible area in each TPI class per fire zone unit."}
    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False, index=True)
    tpi_class = Column(Enum(TPIClassEnum), nullable=False)
    fuel_area = Column(Float, nullable=False)
    fuel_type_raster_id = Column(Integer, ForeignKey(FuelTypeRaster.id), nullable=True, index=True)


class AdvisoryShapeFuels(Base):
    """
    Fuel types and their areas in fire zone units.
    """

    __tablename__ = "advisory_shape_fuels"
    __table_args__ = {"comment": "Fuel types and their areas in fire zone units."}
    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False, index=True)
    fuel_type = Column(Integer, ForeignKey(SFMSFuelType.id), nullable=False, index=True)
    fuel_area = Column(Float, nullable=False)
    fuel_type_raster_id = Column(Integer, ForeignKey(FuelTypeRaster.id), nullable=True, index=True)


class AdvisoryHFIWindSpeed(Base):
    """Minimum wind speed for each HFI class, per fire zone."""

    __tablename__ = "advisory_hfi_wind_speed"
    __table_args__ = {
        "comment": "Minimum wind speed for each HFI class, per fire zone. hfi_wind_speed refers to the minimum "
        "wind speed in a fire zone that coincides with hfi pixels meeting or exceeding a certain threshold."
    }

    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False, index=True)
    threshold = Column(
        Integer, ForeignKey(HfiClassificationThreshold.id), nullable=False, index=True
    )
    run_parameters = Column(Integer, ForeignKey(RunParameters.id), nullable=False, index=True)
    min_wind_speed = Column(Float, nullable=True)


class AdvisoryHFIPercentConifer(Base):
    """Minimum percent conifer for HFI above advisory level (HFI > 4000), per fire zone."""

    __tablename__ = "advisory_hfi_percent_conifer"
    __table_args__ = {
        "comment": "Minimum percent conifer for HFI above advisory level, per fire zone. min_percent_conifer refers to the minimum "
        "percent of conifer trees in a fire zone that coincides with hfi pixels exceeding an HFI value of 4000."
    }

    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False, index=True)
    fuel_type = Column(Integer, ForeignKey(SFMSFuelType.id), nullable=False)
    run_parameters = Column(Integer, ForeignKey(RunParameters.id), nullable=False, index=True)
    min_percent_conifer = Column(Integer, nullable=True)
    fuel_type_raster_id = Column(Integer, ForeignKey(FuelTypeRaster.id), nullable=True, index=True)


class CombustibleArea(Base):
    """The combustible area of each advisory shape (aka fire zone unit) per fuel grid."""

    __tablename__ = "combustible_area"
    __table_args__ = {
        "comment": "The combustible area of advisory shapes for each unique fuel grid."
    }

    id = Column(Integer, primary_key=True, index=True)
    advisory_shape_id = Column(Integer, ForeignKey(Shape.id), nullable=False, index=True)
    combustible_area = Column(Float, nullable=False)
    fuel_type_raster_id = Column(Integer, ForeignKey(FuelTypeRaster.id), nullable=False, index=True)
