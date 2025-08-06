from unittest.mock import Mock, patch

from aws_mp_utils.scripts.cli_utils import get_config, get_mp_client


@patch('aws_mp_utils.scripts.cli_utils.echo_style')
def test_get_config_not_found(mock_echo):
    # File not found
    context = {'config_file': 'tests/data/noconfig.yaml'}
    get_config(context)
    mock_echo.assert_called_once_with(
        'Config file: tests/data/noconfig.yaml not found. '
        'Using default configuration values.',
        no_color=True
    )


@patch('sys.exit')
@patch('aws_mp_utils.scripts.cli_utils.echo_style')
def test_get_config_invalid(mock_echo, mock_exit):
    # Invalid config value
    context = {'config_file': 'tests/data/invalidconfig.yaml'}
    get_config(context)
    mock_exit.assert_called_once_with(1)


@patch('aws_mp_utils.scripts.cli_utils.get_client')
@patch('aws_mp_utils.scripts.cli_utils.get_session')
def test_get_mp_client(mock_get_session, mock_get_client):
    client = Mock()
    mock_get_client.return_value = client
    res_client = get_mp_client('profile', 'us-east-1')
    assert res_client == client
