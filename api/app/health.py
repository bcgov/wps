""" Module to perform health checks.
"""
import requests
import logging
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
    readyCount = resp_json.get('status').get('readyReplicas')
    replicaCount = resp_json.get('status').get('replicas')
    if readyCount > 1:
        healthy = True
        message = 'Healthy ({} out of {} pods are ready)'.format(
            readyCount,
            replicaCount)
    else:
        healthy = False
        message = 'Only {} out of {} pods are healthy'.format(
            readyCount, replicaCount)
    if readyCount < replicaCount:
        logger.error(message)
    else:
        logger.info(message)
    return {"message": message, "healthy": healthy}
