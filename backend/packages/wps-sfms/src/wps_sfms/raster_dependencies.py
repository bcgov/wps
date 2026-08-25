"""Shared loading and validation for raster calculation dependencies."""

from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from typing import Callable, ContextManager, Generator

from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.sfms.raster_addresser import GDALPath
from wps_shared.utils.s3_client import S3Client

MultiDatasetContext = Callable[[list[GDALPath]], ContextManager[list[WPSDataset]]]


class GriddedRasterDependencies:
    """Load raster dependencies and validate them against a fuel reference grid."""

    @staticmethod
    async def assert_keys_exist(
        s3_client: S3Client,
        keys: Iterable[GDALPath],
    ) -> None:
        """Raise when any required raster is missing from object storage."""
        dependency_keys = tuple(keys)
        if not await s3_client.all_objects_exist(*dependency_keys):
            details = ", ".join(str(key) for key in dependency_keys)
            raise RuntimeError(f"Missing raster dependencies: {details}")

    @staticmethod
    def index_by_key(datasets: Iterable[WPSDataset]) -> dict[str, WPSDataset]:
        """Index opened datasets by their source path so returned order does not matter."""
        return {dataset.ds_path: dataset for dataset in datasets if dataset.ds_path is not None}

    @contextmanager
    def open_by_key(
        self,
        input_dataset_context: MultiDatasetContext,
        keys: Iterable[GDALPath],
    ) -> Generator[dict[str, WPSDataset], None, None]:
        """Open all requested rasters and yield them indexed by source path."""
        dependency_keys = list(keys)
        with input_dataset_context(dependency_keys) as datasets:
            yield self.index_by_key(datasets)

    @staticmethod
    def validate_grids(
        reference: WPSDataset,
        candidates: Mapping[str, WPSDataset],
    ) -> None:
        """Validate that candidate rasters use the fuel reference grid.

        Candidate mapping keys are error-message labels. Raster paths come from the opened
        datasets.
        """
        reference_dataset = reference.as_gdal_ds()
        for label, dataset in candidates.items():
            if not rasters_match(dataset.as_gdal_ds(), reference_dataset):
                raise ValueError(
                    f"{label} raster does not match the fuel grid: "
                    f"{dataset.ds_path} vs {reference.ds_path}"
                )
