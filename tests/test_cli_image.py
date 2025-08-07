from unittest.mock import patch

from click.testing import CliRunner

from aws_mp_utils.scripts.cli import main


# -------------------------------------------------
@patch('aws_mp_utils.scripts.image.start_mp_change_set')
@patch('aws_mp_utils.scripts.image.get_image_delivery_option_id')
@patch('aws_mp_utils.scripts.image.get_mp_client')
def test_restrict_version(
    mock_client,
    mock_get_delivery_id,
    mock_start_change_set
):
    """Confirm restrict image version"""
    mock_get_delivery_id.return_value = '12345'
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'image', 'restrict-version',
        '--config-file', 'tests/data/config.yaml',
        '--entity-id', '00000000-0000-4000-8000-000000000001',
        '--ami-id', 'ami-12345',
        '--max-rechecks', 10,
        '--conflict-wait-period', 300,
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Failure to start changeset
    mock_start_change_set.side_effect = Exception('Invalid change set!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Invalid change set!' in result.output

    # Simulate failure in boto3
    mock_get_delivery_id.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output
