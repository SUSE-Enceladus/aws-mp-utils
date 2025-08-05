import pytest

from unittest.mock import Mock, patch

from aws_mp_utils.auth import get_session, get_client
from aws_mp_utils.exceptions import AWSMPUtilsException


@patch('aws_mp_utils.auth.boto3')
def test_get_session(mock_boto3):
    session = Mock()
    mock_boto3.Session.return_value = session

    # Get session from keys
    result = get_session('123456', 'abc123')
    assert session == result

    # Get session from profile name
    result = get_session(profile_name='profile-1')
    assert session == result

    # Missing creds failure
    with pytest.raises(AWSMPUtilsException):
        get_session()


@patch('aws_mp_utils.auth.boto3')
def test_get_client(mock_boto3):
    client = Mock()
    session = Mock()
    session.client.return_value = client
    mock_boto3.session.Session.return_value = session

    result = get_client('marketplace-catalog', 'us-east-1', session)
    assert client == result
    session.client.assert_called_once_with(
        service_name='marketplace-catalog',
        region_name='us-east-1',
    )
