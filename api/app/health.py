""" Module to perform health checks.
"""
import logging
import requests
from wps_shared import config

logger = logging.getLogger(__name__)


def url_join(parts):
    """Take various parts of a url and join them"""
    return "/".join(map(lambda part: part.strip("/"), parts))


def crunchydb_cluster_health_check():
    """ Makes call to Patroni cluster namespace in Openshift to retrieve the statuses of all
    individual Patroni pods, then re-formats response """
    parts = [
        config.get('OPENSHIFT_BASE_URI'),
        config.get('OPENSHIFT_NAMESPACE_API'),
        config.get('PROJECT_NAMESPACE'),
        'postgresclusters/',
        config.get('PATRONI_CLUSTER_NAME')
    ]
    # form URL by concatenating all substrings in parts[], making sure there's exactly 1 / between each part
    url = url_join(parts)
    header = {
        'Authorization': 'Bearer ' + config.get('STATUS_CHECKER_SECRET')
    }
    resp = requests.get(url, headers=header, timeout=10)
    resp_json = resp.json()
    logger.info(resp_json)
    # NOTE: In Openshift parlance "replica" refers to how many of one pod we have, in CrunchyDB's managed
    # Patroni, a "Replica" refers to a read only copy of of the Leader.
    # Get the number of pods that are ready:
    ready_count = resp_json.get('status').get('instances')[0].get('readyReplicas')
    # Get the number of pods we expect:
    replica_count = resp_json.get('status').get('instances')[0].get('replicas')
    if ready_count > 1:
        # It's actually a bit more complicated than this.
        # There are a number of scenarios that are ok:
        # e.g. Leader is up, and one ore more patroni replicas are somewhat lagging.
        # e.g. Leader is up, and there's one patroni replica.
        # There are scenarios that are bad:
        # e.g. Leader is up, and there are no patroni replicas. (Bots work, but website would be down)
        # e.g. Leader is down, replicas are up.
        # For now, we assume that if there's more than one pod, that all is well.
        healthy = True
        message = f"Healthy ({ready_count} out of {replica_count} pods are ready)"
    else:
        healthy = False
        message = f"Only {ready_count} out of {replica_count} pods are healthy"
    if ready_count < replica_count:
        logger.error(message)
    else:
        logger.debug(message)
    return {"message": message, "healthy": healthy}
