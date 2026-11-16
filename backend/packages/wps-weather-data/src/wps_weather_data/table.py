"""What the station weather Delta Lake tables have in common: where they live in object storage,
how Delta Lake reaches them, and their upkeep."""

from deltalake import DeltaTable
from wps_shared import config
from wps_shared.sfms.raster_addresser import S3Key

from wps_weather_data.addresser import StationWeatherAddresser

# How far back a table can be read as it was. Files older than this that no current version
# refers to are deleted by `maintain`.
VACUUM_RETENTION_HOURS = 30 * 24


def object_store_options() -> dict[str, str]:
    """Delta Lake storage options for our object store.

    `conditional_put` is what makes several writers per table safe: the store rejects a commit
    whose log entry already exists. Checked with backend/scripts/object_store_delta_check.py.
    """
    return {
        "AWS_ENDPOINT_URL": f"https://{config.get('OBJECT_STORE_SERVER')}",
        "AWS_ACCESS_KEY_ID": config.get("OBJECT_STORE_USER_ID"),
        "AWS_SECRET_ACCESS_KEY": config.get("OBJECT_STORE_SECRET"),
        "AWS_REGION": "us-east-1",
        "conditional_put": "etag",
    }


class DeltaWeatherTable:
    """A station weather Delta Lake table.

    Create one and reuse it: creating it reads settings but does not contact the object store.
    With no `table_uri`, the table is the one the addresser names, in our object store.
    """

    def __init__(self, table_uri: str | None = None, storage_options: dict[str, str] | None = None):
        if table_uri is None:
            addresser = StationWeatherAddresser()
            table_uri = addresser.delta_uri(self.get_key(addresser))
            storage_options = object_store_options()
        self.table_uri = table_uri
        self.storage_options = storage_options

    def get_key(self, addresser: StationWeatherAddresser) -> S3Key:
        """The table's S3 key."""
        raise NotImplementedError

    def exists(self) -> bool:
        return DeltaTable.is_deltatable(self.table_uri, storage_options=self.storage_options)

    def open(self) -> DeltaTable:
        return DeltaTable(self.table_uri, storage_options=self.storage_options)

    def maintain(
        self,
        *,
        retention_hours: int = VACUUM_RETENTION_HOURS,
        enforce_retention_duration: bool = True,
    ) -> dict:
        """Compact, checkpoint and vacuum the table. Returns what each step did.

        `optimize` merges the small files that appends and merges leave, a checkpoint keeps the
        transaction log quick to open, and `vacuum` deletes files that no table version within
        the retention window refers to.
        """
        table = self.open()
        compacted = table.optimize.compact()
        table.create_checkpoint()
        table.cleanup_metadata()
        deleted = table.vacuum(
            retention_hours=retention_hours,
            dry_run=False,
            enforce_retention_duration=enforce_retention_duration,
        )
        return {
            "files_added": compacted["numFilesAdded"],
            "files_removed": compacted["numFilesRemoved"],
            "files_deleted": len(deleted),
        }
