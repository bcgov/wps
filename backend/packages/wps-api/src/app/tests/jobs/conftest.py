import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName


@pytest.fixture
def tracked_jobs(mocker: MockerFixture) -> list[SFMSRunLogJobName]:
    """Run SFMS tracked jobs without the run log, collecting the job names they ran under."""
    job_names = []

    def track_sfms_run(job_name, _sfms_run_id):
        def decorator(fn):
            async def wrapper(*args, **kwargs):
                job_names.append(job_name)
                return await fn(*args, **kwargs)

            return wrapper

        return decorator

    mocker.patch("app.jobs.sfms_run_pipeline.track_sfms_run", side_effect=track_sfms_run)
    return job_names
