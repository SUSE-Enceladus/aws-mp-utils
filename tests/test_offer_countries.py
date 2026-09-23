from unittest.mock import MagicMock
import pytest

from aws_mp_utils.exceptions import AWSMPUtilsException
from aws_mp_utils.product import get_public_offer_id_for_product
from aws_mp_utils.offer_countries import (
    get_available_countries,
    create_update_targeting_change_doc
)


def test_get_public_offer_id_for_product():
    """Confirm retrieving public offer_id from product_id"""
    mock_client = MagicMock()
    mock_client.list_entities.return_value = {
        'EntitySummaryList': [
            {'EntityId': 'offer-9999'}
        ]
    }

    offer_id = get_public_offer_id_for_product(mock_client, 'prod-1234')
    assert offer_id == 'offer-9999'
    mock_client.list_entities.assert_called_once_with(
        Catalog='AWSMarketplace',
        EntityType='Offer',
        EntityTypeFilters={
            'OfferFilters': {
                'ProductId': {
                    'ValueList': ['prod-1234']
                },
                'Targeting': {
                    'ValueList': ['CountryCodes', 'None']
                },
                'State': {
                    'ValueList': ['Draft', 'Released']
                }
            }
        }
    )


def test_get_public_offer_id_for_product_not_found():
    """Confirm exception raised when public offer not found for product_id"""
    mock_client = MagicMock()
    mock_client.list_entities.return_value = {
        'EntitySummaryList': []
    }

    with pytest.raises(AWSMPUtilsException) as exc_info:
        get_public_offer_id_for_product(mock_client, 'prod-invalid')
    assert "No public offer found for product ID 'prod-invalid'." in str(
        exc_info.value
    )


def test_get_available_countries_with_offer_id():
    """Confirm get available countries directly with offer_id"""
    mock_client = MagicMock()
    mock_client.describe_entity.return_value = {
        'DetailsDocument': {
            'Rules': [
                {
                    'Type': 'TargetingRule',
                    'PositiveTargeting': {
                        'CountryCodes': ['US', 'DE', 'FR']
                    }
                }
            ]
        }
    }

    countries = get_available_countries(
        client=mock_client,
        offer_id='offer-12345'
    )
    assert countries == ['DE', 'FR', 'US']


def test_get_available_countries_with_product_id():
    """Confirm get available countries via product_id resolution"""
    mock_client = MagicMock()
    mock_client.list_entities.return_value = {
        'EntitySummaryList': [
            {'EntityId': 'offer-12345'}
        ]
    }
    mock_client.describe_entity.return_value = {
        'DetailsDocument': {
            'Rules': [
                {
                    'Type': 'TargetingRule',
                    'PositiveTargeting': {
                        'CountryCodes': ['GB', 'CA']
                    }
                }
            ]
        }
    }

    countries = get_available_countries(
        client=mock_client,
        product_id='prod-12345'
    )
    assert countries == ['CA', 'GB']


def test_get_available_countries_no_ids():
    """Confirm exception raised when neither product_id nor offer_id given"""
    mock_client = MagicMock()
    with pytest.raises(AWSMPUtilsException) as exc_info:
        get_available_countries(client=mock_client)
    assert "Either 'product_id' or 'offer_id' must be provided." in str(
        exc_info.value
    )


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


def test_get_available_countries_both_ids():
    """Confirm exception raised when both product_id and offer_id given"""
    mock_client = MagicMock()
    with pytest.raises(AWSMPUtilsException) as exc_info:
        get_available_countries(
            client=mock_client,
            product_id='prod-12345',
            offer_id='offer-12345'
        )
    assert "Both 'product_id' and 'offer_id' cannot be provided at the same time." in str(
        exc_info.value
    )
