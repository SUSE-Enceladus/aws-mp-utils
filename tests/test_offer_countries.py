from unittest.mock import MagicMock

from aws_mp_utils.offer_countries import (
    get_available_countries,
    create_update_targeting_change_doc
)


def test_get_available_countries():
    """Confirm get available countries extracts and sorts country codes"""
    mock_client = MagicMock()
    mock_client.describe_entity.return_value = {
        'DetailsDocument': {
            'Targeting': {
                'PositiveTargeting': {
                    'CountryCodes': ['US', 'DE', 'FR']
                }
            }
        }
    }

    countries = get_available_countries(mock_client, 'offer-12345')
    assert countries == ['DE', 'FR', 'US']
    mock_client.describe_entity.assert_called_once_with(
        Catalog='AWSMarketplace',
        EntityId='offer-12345'
    )


def test_get_available_countries_empty():
    """Confirm get available countries returns empty list when none found"""
    mock_client = MagicMock()
    mock_client.describe_entity.return_value = {
        'DetailsDocument': {}
    }

    countries = get_available_countries(mock_client, 'offer-12345')
    assert countries == []


def test_create_update_targeting_change_doc():
    """Confirm UpdateTargeting change document structure"""
    doc = create_update_targeting_change_doc('offer-12345', ['us', 'de'])
    expected = {
        'ChangeType': 'UpdateTargeting',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': 'offer-12345'
        },
        'DetailsDocument': {
            'PositiveTargeting': {
                'CountryCodes': ['US', 'DE']
            }
        }
    }
    assert doc == expected
