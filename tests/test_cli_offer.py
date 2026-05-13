from unittest.mock import patch

from click.testing import CliRunner

from aws_mp_utils.scripts.cli import main


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.start_mp_change_set')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_update_information(
    mock_client,
    mock_start_change_set
):
    """Confirm update offer information"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'offer', 'update-information',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--name', 'Offer name',
        '--description', 'Offer description',
        '--acquisition-channel', 'External',
        '--pricing-model', 'Contract',
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
