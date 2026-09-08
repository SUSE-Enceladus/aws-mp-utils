# -*- coding: utf-8 -*-

"""aws-mp-utils AWS Marketplace Catalog utilities."""

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

import boto3
import jmespath

from aws_mp_utils.exceptions import AWSMPUtilsException
from aws_mp_utils.offer import get_offer_id_for_product


def get_available_countries(
    client: boto3.client,
    product_id: str = None,
    offer_id: str = None,
    catalog: str = 'AWSMarketplace'
) -> list[str]:
    """
    Lists the available target countries where an offer can be sold.

    :param client: boto3 marketplace-catalog client instance.
    :param product_id: The unique identifier of the product in the
        AWS Marketplace.
    :param offer_id: The unique identifier of the offer in the
        AWS Marketplace. If not provided, it will be retrieved using
        the product_id.
    :param catalog: The catalog name (default: 'AWSMarketplace').
    :return: A sorted list of 2-letter ISO country codes
        (e.g., ['DE', 'FR', 'US']).
    """
    if not offer_id:
        if not product_id:
            raise AWSMPUtilsException(
                "Either 'product_id' or 'offer_id' must be provided."
            )
        offer_id = get_offer_id_for_product(
            client=client,
            product_id=product_id,
            catalog=catalog
        )

    entity = client.describe_entity(
        Catalog=catalog,
        EntityId=offer_id
    )

    """
    Example describe entity output:
    {
        "DetailsDocument": {
            "Rules": [
                {
                    "Type": "TargetingRule",
                    "PositiveTargeting": {
                        "CountryCodes": [
                            "US",
                            "DE",
                            "FR"
                        ]
                    }
                }
            ]
        }
    }
    """

    details = entity['DetailsDocument']
    query = (
        "Rules[?Type=='TargetingRule'] | [0]"
        ".PositiveTargeting.CountryCodes"
    )
    country_codes = jmespath.search(query, details)

    if country_codes is None:
        return []
    return sorted(country_codes)


def create_update_targeting_change_doc(
    offer_id: str,
    country_codes: list[str]
) -> dict:
    """
    Creates an update offer request dictionary to set available
    target countries.

    :param offer_id: The unique identifier of the offer in the
        AWS Marketplace.
    :param country_codes: A list of 2-letter ISO country codes
        (e.g., ['US', 'DE', 'FR']).
    :return: A dictionary structured for an UpdateTargeting change set.
    """
    data = {
        'ChangeType': 'UpdateTargeting',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': offer_id
        },
        'DetailsDocument': {
            'PositiveTargeting': {
                'CountryCodes': [code.upper() for code in country_codes]
            }
        }
    }
    return data
