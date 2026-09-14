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
@patch('aws_mp_utils.scripts.offer.get_available_countries')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_list_available_countries(
    mock_client,
    mock_get_available_countries
):
    """Confirm list available countries"""
    mock_get_available_countries.return_value = [
        "DE", "FR", "US"
    ]

    args = [
        'offer', 'list-available-countries',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'DE,FR,US' in result.output

    # No available countries found
    mock_get_available_countries.return_value = []
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'No targeted country codes found for this offer.' in result.output

    # Failure
    mock_get_available_countries.side_effect = Exception('Some error')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Some error' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.get_public_offer_id_for_product')
@patch('aws_mp_utils.scripts.offer.start_mp_change_set')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_set_available_countries(
    mock_client,
    mock_start_change_set,
    mock_get_public_offer_id_for_product
):
    """Confirm set offer available countries with product-id"""
    mock_get_public_offer_id_for_product.return_value = 'offer-123456789'
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'offer', 'set-available-countries',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-123456789',
        '--country-codes', 'US,DE,FR',
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

    # Simulate failure in boto3 (outer exception block)
    mock_client.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output


def test_countries_usage_error():
    """Confirm missing options error for countries commands"""
    args = [
        'offer', 'list-available-countries'
    ]
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--product-id', '--offer-id'] parameters is required."
    ) in result.output

    args = [
        'offer', 'set-available-countries',
        '--country-codes', 'US,DE'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--product-id', '--offer-id'] parameters is required."
    ) in result.output
