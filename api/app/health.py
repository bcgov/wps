""" Module to perform health checks.
"""
import requests
from app import config


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
    url = "/".join(map(lambda part: part.strip('/'), parts))
    header = {
        'Authorization': 'Bearer ' + config.get('STATUS_CHECKER_SECRET')
    }
    resp = requests.get(url, headers=header)
    resp_json = resp.json()
    if resp_json.get('status').get('replicas') == resp_json.get('status').get('readyReplicas'):
        healthy = True
        message = 'Healthy as ever'
    else:
        healthy = False
        message = 'Only %s out of %s pods are healthy' % (
            resp_json.get('status').get('readyReplicas'),
            resp_json.get('status').get('replicas')
        )
    return {"message": message, "healthy": healthy}
