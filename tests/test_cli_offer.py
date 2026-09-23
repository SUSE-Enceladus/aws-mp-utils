import json
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
@patch('aws_mp_utils.scripts.offer.get_offer_prices')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_list_prices(
    mock_client,
    mock_get_offer_prices,
    tmp_path
):
    """Confirm list offer prices"""
    mock_get_offer_prices.return_value = [
        {
            "Type": "UsageBasedPricingTerm",
            "CurrencyCode": "USD"
        }
    ]

    args = [
        'offer', 'list-prices',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'UsageBasedPricingTerm' in result.output

    # Test output to file
    out_file = tmp_path / "prices.json"
    args_file = args + ['--output-file', str(out_file)]
    result = runner.invoke(main, args_file)
    assert result.exit_code == 0
    assert out_file.exists()
    assert 'UsageBasedPricingTerm' in out_file.read_text()

    # Failure
    mock_get_offer_prices.side_effect = Exception('Some error')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Some error' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.start_mp_change_set')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_update_prices(
    mock_client,
    mock_start_change_set
):
    """Confirm update offer prices"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'offer', 'update-prices',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--details-document', '[{"Type": "UsageBasedPricingTerm"}]',
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


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.start_mp_change_set')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_update_prices_with_file(
    mock_client,
    mock_start_change_set,
    tmp_path
):
    """Confirm update offer prices with a file"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    doc_file = tmp_path / "terms.json"
    doc_file.write_text('[{"Type": "UsageBasedPricingTerm"}]')

    args = [
        'offer', 'update-prices',
        '--config-file', 'tests/data/config.yaml',
        '--offer-id', '123456789',
        '--details-document-file', str(doc_file),
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output


def test_prices_usage_error(tmp_path):
    """Confirm offer prices usage error"""
    args = [
        'offer', 'list-prices',
        '--product-id', 'prod-12345',
        '--offer-id', 'offer-12345'
    ]
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "Both '--product-id' and '--offer-id' cannot be provided at the same time."
    ) in result.output

    args = [
        'offer', 'list-prices'
    ]
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--product-id', '--offer-id'] parameters is required."
    ) in result.output

    args = [
        'offer', 'update-prices',
        '--offer-id', '123456789'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--details-document-file', "
        "'--details-document'] parameters is required to update "
        "prices in an offer."
    ) in result.output

    args = [
        'offer', 'update-prices',
        '--offer-id', '123456789',
        '--details-document', 'invalid_json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output

    args = [
        'offer', 'update-prices',
        '--offer-id', '123456789',
        '--details-document-file', 'non_existing_file.json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "File --details-document-file not found:" in result.output

    invalid_file = tmp_path / 'invalid.json'
    invalid_file.write_text('invalid_json')
    args = [
        'offer', 'update-prices',
        '--offer-id', '123456789',
        '--details-document-file', str(invalid_file)
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert ("Invalid JSON provided in file "
            "--details-document-file:") in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.get_available_countries')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_list_countries(
    mock_client,
    mock_get_available_countries,
    tmp_path
):
    """Confirm list available countries"""
    mock_get_available_countries.return_value = [
        "DE", "FR", "US"
    ]

    args = [
        'offer', 'list-countries',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'DE,FR,US' in result.output

    # Test output to file
    out_file = tmp_path / "countries.json"
    args_file = args + ['-o', str(out_file)]
    result = runner.invoke(main, args_file)
    assert result.exit_code == 0
    assert out_file.exists()
    assert json.loads(out_file.read_text()) == ["DE", "FR", "US"]

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
def test_update_countries(
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
        'offer', 'update-countries',
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

    # Test with --countries
    args_countries = [
        'offer', 'update-countries',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-123456789',
        '--countries', 'US,DE,FR',
        '--no-color'
    ]
    result = runner.invoke(main, args_countries)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Test with --details-document
    args_doc = [
        'offer', 'update-countries',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-123456789',
        '--details-document', '["US", "DE", "FR"]',
        '--no-color'
    ]
    result = runner.invoke(main, args_doc)
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


# -------------------------------------------------
@patch('aws_mp_utils.scripts.offer.get_public_offer_id_for_product')
@patch('aws_mp_utils.scripts.offer.start_mp_change_set')
@patch('aws_mp_utils.scripts.offer.get_mp_client')
def test_update_countries_with_file(
    mock_client,
    mock_start_change_set,
    mock_get_public_offer_id_for_product,
    tmp_path
):
    """Confirm update offer countries with a file"""
    mock_get_public_offer_id_for_product.return_value = 'offer-123456789'
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    doc_file = tmp_path / "countries.json"
    doc_file.write_text('["US", "DE", "FR"]')

    args = [
        'offer', 'update-countries',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-123456789',
        '--details-document-file', str(doc_file),
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Test with --countries-file
    txt_file = tmp_path / "countries.txt"
    txt_file.write_text('US, DE, FR')

    args_txt = [
        'offer', 'update-countries',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-123456789',
        '--countries-file', str(txt_file),
        '--no-color'
    ]
    result = runner.invoke(main, args_txt)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output


def test_countries_usage_error(tmp_path):
    """Confirm missing options error for countries commands"""
    args = [
        'offer', 'list-countries',
        '--product-id', 'prod-12345',
        '--offer-id', 'offer-12345'
    ]
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "Both '--product-id' and '--offer-id' cannot be provided at the same time."
    ) in result.output

    args = [
        'offer', 'list-countries'
    ]
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--product-id', '--offer-id'] parameters is required."
    ) in result.output

    args = [
        'offer', 'update-countries',
        '--offer-id', '123456789'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--details-document-file', "
        "'--details-document'] parameters is required to update "
        "countries in an offer."
    ) in result.output

    args = [
        'offer', 'update-countries',
        '--offer-id', '123456789',
        '--details-document', '{"invalid":'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output

    args = [
        'offer', 'update-countries',
        '--offer-id', '123456789',
        '--details-document-file', 'non_existing_file.json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "File --details-document-file not found:" in result.output

    invalid_file = tmp_path / 'invalid.json'
    invalid_file.write_text('{"invalid":')
    args = [
        'offer', 'update-countries',
        '--offer-id', '123456789',
        '--details-document-file', str(invalid_file)
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert ("Invalid JSON provided in file "
            "--details-document-file:") in result.output
