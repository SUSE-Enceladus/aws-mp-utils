# -*- coding: utf-8 -*-

"""aws-mp-utils AWS Marketplace Catalog utilities for offer prices."""

# Copyright (c) 2026 SUSE LLC
#
# This file is part of aws_mp_utils. aws_mp_utils provides an
# api and command line utilities for handling marketplace catalog API
# in the AWS Cloud.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import boto3
import jmespath

from aws_mp_utils.exceptions import AWSMPUtilsException
from aws_mp_utils.product import get_public_offer_id_for_product


def get_offer_prices(
    client: boto3.client,
    product_id: str = None,
    offer_id: str = None,
    catalog: str = 'AWSMarketplace'
) -> list[dict]:
    """
    Lists the pricing terms for an offer.

    :param client: boto3 marketplace-catalog client instance.
    :param product_id: The unique identifier of the product in the
        AWS Marketplace.
    :param offer_id: The unique identifier of the offer in the
        AWS Marketplace. If not provided, it will be retrieved using
        the product_id.
    :param catalog: The catalog name (default: 'AWSMarketplace').
    :return: A list of terms dictionary objects from DetailsDocument.Terms,
        excluding LegalTerm and SupportTerm.
    """
    if product_id and offer_id:
        raise AWSMPUtilsException(
            "Both 'product_id' and 'offer_id' cannot be provided at the same time."
        )

    if not offer_id:
        if not product_id:
            raise AWSMPUtilsException(
                "Either 'product_id' or 'offer_id' must be provided."
            )
        offer_id = get_public_offer_id_for_product(
            client=client,
            product_id=product_id,
            catalog=catalog
        )

    entity = client.describe_entity(
        Catalog=catalog,
        EntityId=offer_id
    )

    details = entity['DetailsDocument']
    if isinstance(details, str):
        details = json.loads(details)

    terms = jmespath.search("Terms", details)

    if terms is None:
        return []

    excluded_types = ('LegalTerm', 'SupportTerm')
    return [
        term for term in terms
        if isinstance(term, dict) and term.get('Type') not in excluded_types
    ]


def create_update_pricing_change_doc(
    offer_id: str,
    details_document: str,
    pricing_model: str = 'Usage'
) -> dict:
    """
    Creates an update offer request dictionary to set pricing terms.

    :param offer_id: The unique identifier of the offer in the
        AWS Marketplace.
    :param details_document: A JSON formatted string containing the
        pricing details or terms document.
    :param pricing_model: The pricing model for the offer
        (default: 'Usage').
    :return: A dictionary structured for an UpdatePricingTerms change set.
    """
    parsed = json.loads(details_document)
    if isinstance(parsed, list):
        details_doc = {
            'PricingModel': pricing_model,
            'Terms': parsed
        }
    elif isinstance(parsed, dict):
        details_doc = parsed
        if 'PricingModel' not in details_doc:
            details_doc['PricingModel'] = pricing_model
    else:
        raise AWSMPUtilsException("Invalid details document format.")

    data = {
        'ChangeType': 'UpdatePricingTerms',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': offer_id
        },
        'DetailsDocument': details_doc
    }
    return data
