"""Opt-in prefix for object-store keys.

``OBJECT_STORE_KEY_PREFIX`` is unset by default. When it is unset or empty,
keys are returned unchanged so production and OpenShift paths stay
byte-identical. When set (for example ``local/<username>``), it is applied
to keys built by the API and jobs Python key builders.

Trailing slashes are normalized so ``local/user`` and ``local/user/`` both
become ``local/user/``.

Jobs that write to object storage outside these Python key builders do not
honor the prefix:

- openshift/pgslice/docker/partition_and_archive.sh (``s3://$AWS_BUCKET/retired/...``)
- openshift/hourlies-prune/docker/prune_hourlies.sh (``s3://$AWS_BUCKET/sfms/uploads/hourlies/...``)
- openshift/s3-backup/docker/prune.py (lists and deletes in ``AWS_BUCKET``)
- openshift/s3-backup/docker/backup_to_s3.sh (``s3://$AWS_BUCKET/backup/...``)
- openshift/s3-backup/docker/cleanup_bucket.sh (``s3://$AWS_BUCKET/pgbackrest/...`` and ``s3://$AWS_BUCKET/backup/...``)
"""

import os

from wps_shared import config

OBJECT_STORE_KEY_PREFIX_ENV = "OBJECT_STORE_KEY_PREFIX"


def get_object_store_key_prefix() -> str:
    """Return the normalized prefix, or ``""`` when the env var is unset or empty.

    Reads ``os.environ`` directly so an unset value does not log a missing-variable
    warning, and so stubs of ``config.get`` cannot break or hijack this lookup.
    """
    raw = os.environ.get(OBJECT_STORE_KEY_PREFIX_ENV, "")
    if raw is None:
        return ""
    normalized = str(raw).strip().strip("/")
    if not normalized:
        return ""
    return f"{normalized}/"


def object_store_key(key: str) -> str:
    """Prefix an object-store key when ``OBJECT_STORE_KEY_PREFIX`` is set.

    When the prefix is unset or empty, ``key`` is returned unchanged.
    Applying the helper twice is a no-op.
    """
    prefix = get_object_store_key_prefix()
    if not prefix:
        return key
    if str(key).startswith(prefix):
        return key
    return prefix + str(key).lstrip("/")


def object_store_gdal_path(relative_key: str, bucket: str | None = None) -> str:
    """Return a ``/vsis3/{bucket}/{prefixed-key}`` path for a plain object key."""
    if bucket is None:
        bucket = config.get("OBJECT_STORE_BUCKET")
    return f"/vsis3/{bucket}/{object_store_key(relative_key)}"
