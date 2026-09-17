import json
from unittest.mock import MagicMock
import pytest

from aws_mp_utils.exceptions import AWSMPUtilsException
from aws_mp_utils.offer_prices import (
    get_offer_prices,
    create_update_pricing_change_doc
)


def test_get_offer_prices_excludes_legal_and_support_terms():
    """Confirm get_offer_prices filters out LegalTerm and SupportTerm."""
    mock_client = MagicMock()
    all_terms = [
        {"Type": "UsageBasedPricingTerm", "CurrencyCode": "USD"},
        {"Type": "LegalTerm", "Documents": []},
        {"Type": "SupportTerm", "RefundPolicy": "None"},
        {"Type": "FreeTrialPricingTerm"}
    ]
    mock_client.describe_entity.return_value = {
        'DetailsDocument': {
            'Terms': all_terms
        }
    }

    terms = get_offer_prices(
        client=mock_client,
        offer_id='offer-12345'
    )
    assert len(terms) == 2
    assert terms[0]["Type"] == "UsageBasedPricingTerm"
    assert terms[1]["Type"] == "FreeTrialPricingTerm"


def test_get_offer_prices_with_product_id():
    """Confirm get offer prices via product_id resolution."""
    mock_client = MagicMock()
    mock_client.list_entities.return_value = {
        'EntitySummaryList': [
            {'EntityId': 'offer-12345'}
        ]
    }
    expected_terms = [
        {"Type": "FreeTrialPricingTerm"}
    ]
    mock_client.describe_entity.return_value = {
        'DetailsDocument': json.dumps({
            'Terms': expected_terms
        })
    }

    terms = get_offer_prices(
        client=mock_client,
        product_id='prod-12345'
    )
    assert terms == expected_terms


def test_get_offer_prices_no_ids():
    """Confirm exception raised when no ID is provided."""
    mock_client = MagicMock()
    with pytest.raises(AWSMPUtilsException) as exc_info:
        get_offer_prices(client=mock_client)
    assert "Either 'product_id' or 'offer_id' must be provided." in str(
        exc_info.value
    )


def test_create_update_pricing_change_doc_list_input():
    """Confirm UpdatePricingTerms change document with list terms input."""
    terms_json = '[{"Type": "UsageBasedPricingTerm"}]'
    doc = create_update_pricing_change_doc(
        'offer-12345',
        terms_json,
        pricing_model='Usage'
    )
    expected = {
        'ChangeType': 'UpdatePricingTerms',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': 'offer-12345'
        },
        'DetailsDocument': {
            'PricingModel': 'Usage',
            'Terms': [{'Type': 'UsageBasedPricingTerm'}]
        }
    }
    assert doc == expected


def test_create_update_pricing_change_doc_dict_input():
    """Confirm UpdatePricingTerms change document with dict input."""
    terms_json = '{"Terms": [{"Type": "FreeTrialPricingTerm"}]}'
    doc = create_update_pricing_change_doc(
        'offer-12345',
        terms_json,
        pricing_model='Contract'
    )
    expected = {
        'ChangeType': 'UpdatePricingTerms',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': 'offer-12345'
        },
        'DetailsDocument': {
            'PricingModel': 'Contract',
            'Terms': [{'Type': 'FreeTrialPricingTerm'}]
        }
    }
    assert doc == expected
