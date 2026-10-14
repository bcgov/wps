from io import BytesIO
from unittest.mock import MagicMock

from scripts.percentile_calculator.s3_to_dataframe import read_s3_csv_to_pandas


def test_read_s3_csv_uses_local_endpoint_and_credentials(mocker):
    mocker.patch(
        "scripts.percentile_calculator.s3_to_dataframe.config.get",
        side_effect=lambda key: {
            "OBJECT_STORE_BUCKET": "wps-local",
            "OBJECT_STORE_USER_ID": "wps-local",
            "OBJECT_STORE_SECRET": "wps-local-password",
        }[key],
    )
    mocker.patch(
        "scripts.percentile_calculator.s3_to_dataframe.get_endpoint_url",
        return_value="http://127.0.0.1:9000",
    )
    body = BytesIO(b"station,value\nABC,12\n")
    client = MagicMock()
    client.get_object.return_value = {"Body": body}
    session = mocker.patch("scripts.percentile_calculator.s3_to_dataframe.get_session")
    session.return_value.create_client.return_value.__enter__.return_value = client

    result = read_s3_csv_to_pandas("data_dumps/stations.csv")

    session.return_value.create_client.assert_called_once_with(
        "s3",
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id="wps-local",
        aws_secret_access_key="wps-local-password",
    )
    client.get_object.assert_called_once_with(Bucket="wps-local", Key="data_dumps/stations.csv")
    assert result.to_dict("records") == [{"station": "ABC", "value": 12}]
    assert body.closed
