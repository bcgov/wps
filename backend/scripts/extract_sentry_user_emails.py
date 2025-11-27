import requests


def generate_email_list(sentry_api_token: str, sentry_org_slug: str, sentry_project_id: str):
    """
    Generates a newline separated text file of emails. Each email is for a user that has experienced an
    issue according to Sentry in the last 14 days. This list can be used to email outage notifications directly
    to affected users.

    Sentry endpoints used:
    - https://docs.sentry.io/api/events/list-a-projects-issues/
    - https://docs.sentry.io/api/events/list-an-issues-events/


    :param sentry_api_token: Sentry API token, requires read access to issues and events resources
    :param sentry_org_slug: Sentry org slug
    :param sentry_project_id: Sentry project ID
    """
    headers = {"Authorization": f"Bearer {sentry_api_token}"}

    issues_endpoint = f"https://sentry.io/api/0/projects/{sentry_org_slug}/{sentry_project_id}/issues/?statsPeriod=14d"
    issues_response = requests.get(issues_endpoint, headers=headers)
    issues = issues_response.json()

    ids = list()
    email_set = set()
    for issue in issues:
        ids.append(issue["id"])
        endpoint = (
            f"https://sentry.io/api/0/organizations/{sentry_org_slug}/issues/{issue['id']}/events/"
        )
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            events = response.json()
            for event in events:
                if event["user"] is not None and event["user"]["email"] is not None:
                    email_set.add(event["user"]["email"])
        else:
            response.raise_for_status()

    with open("user_emails.txt", "w") as file:
        for email in email_set:
            file.write(email + "\n")
