"""Object store keys for the station weather datasets."""

from wps_shared import config
from wps_shared.sfms.raster_addresser import S3Key

# The deployment suffix of production. Every other suffix (pr-123, ...) is a dev deployment.
PRODUCTION_SUFFIX = "prod"


class StationWeatherAddresser:
    """
    Key addresser for the station weather datasets.

    Production datasets live under `weather/stations/`. Dev deployments share one bucket, so
    each keeps its own copy under `dev/{suffix}/weather/stations/` and no deployment writes
    into another's tables. The deployment suffix comes from the SUFFIX setting; with none set,
    as when running locally, the production root is used.
    """

    def __init__(self):
        self.bucket = config.get("OBJECT_STORE_BUCKET")
        suffix = config.get("SUFFIX")
        if suffix and suffix != PRODUCTION_SUFFIX:
            self.root = f"dev/{suffix}/weather/stations"
        else:
            self.root = "weather/stations"

    def delta_uri(self, key: S3Key) -> str:
        """Return the s3:// URI Delta Lake uses for a plain S3 key."""
        return f"s3://{self.bucket}/{key}"

    def get_runs_key(self) -> S3Key:
        """S3 key of the `runs` Delta table: station values from every model run."""
        return S3Key(f"{self.root}/runs")

    def get_by_time_key(self) -> S3Key:
        """S3 key of the `by_time` Delta table: the newest value per station, time and source."""
        return S3Key(f"{self.root}/by_time")

    def get_wf1_key(self) -> S3Key:
        """S3 key of the `wf1` Delta table: every observation and noon forecast fetched from WF1."""
        return S3Key(f"{self.root}/wf1")

    def get_staging_key(self, model: str) -> S3Key:
        """S3 key of a model's `staging` Delta table: the runs it is still downloading."""
        return S3Key(f"{self.root}/staging/{model.lower()}")

    def get_by_station_key(self) -> S3Key:
        """S3 key of the `by_station` Delta table: the `by_time` rows, laid out by station."""
        return S3Key(f"{self.root}/by_station")
