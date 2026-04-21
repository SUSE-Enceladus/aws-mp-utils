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


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.get_available_dimensions')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_list_dimensions(mock_client, mock_get_available_dimensions):
    """Confirm list offer dimensions"""
    mock_get_available_dimensions.return_value = [
        {
            "Key": "t3.medium",
            "Unit": "Hrs",
            "Types": ["Metered"]
        },
        {
            "Key": "u-3tb1.56xlarge",
            "Unit": "Hrs",
            "Types": ["Metered"]
        }
    ]

    args = [
        'offer', 'list-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 't3.medium' in result.output
    assert 'u-3tb1.56xlarge' in result.output

    # No dimensions found
    mock_get_available_dimensions.return_value = []
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'No dimensions were found' in result.output

    # Failure
    mock_get_available_dimensions.side_effect = Exception('Some error')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Some error' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.start_mp_change_set')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_restrict_dimensions(
    mock_client,
    mock_start_change_set
):
    """Confirm restrict offer dimensions"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'offer', 'restrict-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--details-document', '{"Restrictions": ["t2.micro", "t2.small"]}',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
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


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.start_mp_change_set')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_add_dimensions(
    mock_client,
    mock_start_change_set
):
    """Confirm add offer dimensions"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'offer', 'add-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--details-document', '[{"Key": "t2.micro", "Name": "t2.micro"}]',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
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


def test_dimensions_usage_error():
    """Confirm offer dimensions usage error"""
    args = [
        'offer', 'restrict-dimensions',
        '--offer-id', '123456789'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--details-document-file', "
        "'--details-document'] parameters is required to restrict "
        "dimensions in an offer."
    ) in result.output

    args = [
        'offer', 'restrict-dimensions',
        '--offer-id', '123456789',
        '--details-document', 'invalid_json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.get_available_instance_types')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_list_available_instance_types(mock_client, mock_get_available_instance_types):
    """Confirm list available instance types"""
    mock_get_available_instance_types.return_value = [
        "t3.medium",
        "u-3tb1.56xlarge"
    ]

    args = [
        'offer', 'list-available-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 't3.medium' in result.output
    assert 'u-3tb1.56xlarge' in result.output

    # No available instance types found
    mock_get_available_instance_types.return_value = []
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'No available instance types were found' in result.output

    # Failure
    mock_get_available_instance_types.side_effect = Exception('Some error')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Some error' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.start_mp_change_set')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_restrict_instance_types(
    mock_client,
    mock_start_change_set
):
    """Confirm restrict offer instance types"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'offer', 'restrict-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--details-document', '{"Restrictions": ["t2.micro", "t2.small"]}',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
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


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.start_mp_change_set')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_add_instance_types(
    mock_client,
    mock_start_change_set
):
    """Confirm add offer instance types"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'offer', 'add-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--details-document', '["t2.micro", "t2.small"]',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
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


def test_instance_types_usage_error():
    """Confirm offer instance types usage error"""
    args = [
        'offer', 'restrict-instance-types',
        '--offer-id', '123456789'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--details-document-file', "
        "'--details-document'] parameters is required to restrict "
        "instance types in an offer."
    ) in result.output

    args = [
        'offer', 'restrict-instance-types',
        '--offer-id', '123456789',
        '--details-document', 'invalid_json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output
