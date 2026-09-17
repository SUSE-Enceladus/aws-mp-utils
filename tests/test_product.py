import json
from unittest.mock import MagicMock

import pytest

from aws_mp_utils.exceptions import AWSMPUtilsException
from aws_mp_utils.product import (
    create_update_product_change_doc,
    get_public_offer_id_for_product
)


def test_create_update_product_change_doc():
    expected = {
        'ChangeType': 'UpdateInformation',
        'Entity': {
            'Type': 'Product@1.0',
            'Identifier': 'prod-123456'
        }
    }
    details = {
        'Name': 'Product name',
        'Description': 'Product description'
    }
    expected['Details'] = json.dumps(details)

    actual = create_update_product_change_doc(
        'prod-123456',
        'Product name',
        'Product description'
    )
    assert expected == actual


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
