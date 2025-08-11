import json

from unittest.mock import patch, Mock

from click.testing import CliRunner

from aws_mp_utils.scripts.cli import main


def test_client_help():
    """Confirm aws mp utils --help is successful."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'The command line interface provides ' \
           'AWS Marketplace Catalog utilities' in result.output


def test_print_license():
    runner = CliRunner()
    result = runner.invoke(main, ['--license'])
    assert result.exit_code == 0
    assert result.output == 'GPLv3+\n'


# -------------------------------------------------
@patch('aws_mp_utils.scripts.cli.get_mp_client')
def test_describe_change_set(mock_client):
    """Confirm describe change set"""
    change_set = {
        'ChangeSetId': '12345',
        'ChangeSetArn': 'string',
        'ChangeSetName': 'string',
        'Intent': 'APPLY',
        'StartTime': '2018-02-27T13:45:22Z',
        'EndTime': '2018-02-27T13:45:22Z',
        'Status': 'SUCCEEDED',
        'ChangeSet': [
            {
                'ChangeType': 'string',
                'Entity': {
                    'Type': 'string',
                    'Identifier': 'string'
                },
                'Details': 'string',
                'DetailsDocument': {'changeset': 'details'},
                'ChangeName': 'string'
            },
        ]
    }
    client = Mock()
    client.describe_change_set.return_value = change_set
    mock_client.return_value = client

    args = [
        'describe-change-set',
        '--config-file', 'tests/data/config.yaml',
        '--change-set-id', '12345',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert json.loads(result.output)['ChangeSetId'] == '12345'

    # Simulate failure in boto3
    client.describe_change_set.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.cli.get_mp_client')
@patch('aws_mp_utils.scripts.cli.get_change_set_status')
def test_get_change_set_status(mock_status, mock_client):
    """Confirm get change set status"""
    mock_status.return_value = 'success'

    args = [
        'get-change-set-status',
        '--config-file', 'tests/data/config.yaml',
        '--change-set-id', '12345',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'success' in result.output

    mock_status.return_value = 'applying'
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'applying' in result.output

    mock_status.return_value = 'failed'
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'failed' in result.output

    # Simulate failure in boto3
    mock_status.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output
