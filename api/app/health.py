""" Module to perform health checks.
"""
import logging
import requests
from app import config, url_join

logger = logging.getLogger(__name__)


def patroni_cluster_health_check():
    """ Makes call to Patroni cluster namespace in Openshift to retrieve the statuses of all
    individual Patroni pods, then re-formats response """
    parts = [
        config.get('PATHFINDER_BASE_URI'),
        'apis/apps/v1beta1/namespaces/',
        config.get('PROJECT_NAMESPACE'),
        'statefulsets/',
        config.get('PATRONI_CLUSTER_NAME')
    ]
    # form URL by concatenating all substrings in parts[], making sure there's exactly 1 / between each part
    url = url_join(parts)
    header = {
        'Authorization': 'Bearer ' + config.get('STATUS_CHECKER_SECRET')
    }
    resp = requests.get(url, headers=header)
    resp_json = resp.json()
    # NOTE: In Openshift parlance "replica" refers to how many of one pod we have, in Patroni, a "Replica"
    # refers to a read only copy of of the Leader.
    # Get the number of pods that are ready:
    ready_count = resp_json.get('status').get('readyReplicas')
    # Get the number of pods we expect:
    replica_count = resp_json.get('status').get('replicas')
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
        message = 'Healthy ({} out of {} pods are ready)'.format(
            ready_count,
            replica_count)
    else:
        healthy = False
        message = 'Only {} out of {} pods are healthy'.format(
            ready_count, replica_count)
    if ready_count < replica_count:
        logger.error(message)
    else:
        logger.info(message)
    return {"message": message, "healthy": healthy}
