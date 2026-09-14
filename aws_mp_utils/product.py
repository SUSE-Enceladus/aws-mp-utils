# -*- coding: utf-8 -*-

"""aws-mp-utils AWS Marketplace Catalog utilities for products."""

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

from aws_mp_utils.exceptions import AWSMPUtilsException


def create_update_product_change_doc(
    product_id: str,
    name: str = None,
    description: str = None,
    entity_type: str = 'Product@1.0'
) -> dict:
    """
    Creates an update product request dictionary.
    """
    data = {
        'ChangeType': 'UpdateInformation',
        'Entity': {
            'Type': entity_type,
            'Identifier': product_id
        }
    }
    details = {}

    if name:
        details['Name'] = name

    if description:
        details['Description'] = description

    data['Details'] = json.dumps(details)
    return data


def get_public_offer_id_for_product(
    client: boto3.client,
    product_id: str,
    catalog: str = 'AWSMarketplace'
) -> str:
    """
    Retrieves the public offer ID for a given product ID in AWS Marketplace.
    """
    response = client.list_entities(
        Catalog=catalog,
        EntityType='Offer',
        EntityTypeFilters={
            'OfferFilters': {
                'ProductId': {
                    'ValueList': [product_id]
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

    entity_summary = response.get('EntitySummaryList', [])
    if not entity_summary:
        raise AWSMPUtilsException(
            f"No public offer found for product ID '{product_id}'."
        )

    return entity_summary[0]['EntityId']
