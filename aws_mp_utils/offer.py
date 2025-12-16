# -*- coding: utf-8 -*-

"""aws-mp-utils AWS Marketplace Catalog utilities."""

# Copyright (c) 2025 SUSE LLC
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


def create_update_offer_change_doc(
    offer_id: str,
    name: str = None,
    description: str = None,
    acquisition_channel: str = None,
    pricing_model: str = None
) -> dict:
    """
    Creates an update offer request dictionary.
    """
    data = {
        'ChangeType': 'UpdateInformation',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': offer_id
        }
    }
    details = {}

    if name:
        details['Name'] = name

    if description:
        details['Description'] = description

    if acquisition_channel or pricing_model:
        details['PreExistingAgreement'] = {}

        if acquisition_channel:
            details['PreExistingAgreement']['AcquisitionChannel'] = \
                acquisition_channel

        if pricing_model:
            details['PreExistingAgreement']['PricingModel'] = pricing_model

    data['Details'] = json.dumps(details)
    return data


def get_ami_ids_in_mp_entity(
    client: boto3.client,
    entity_id: str,
    visibility_filter: str = 'Public',
) -> list[str]:
    """
    Provides the ami-ids in the versions for an offer.

    If visibility_filter is set, it only returns AMIs from versions
    with a delivery option matching the visibility filter. If the empty string
    is provided as visiblity_filter no filter is applied.
    """
    entity = client.describe_entity(
        Catalog='AWSMarketplace',
        EntityId=entity_id
    )

    """
    Example describe entity output:
    {
        "Details": {
            "Versions": [
                {
                    "Sources": [
                        {
                            "Image": "ami-123",
                            "Id": "1234"
                        }
                    ],
                    "DeliveryOptions": [
                        {"Visibility": "Public"},
                        ...
                    ]
                }
            ]
        }
    }
    """

    details = entity['DetailsDocument']

    if visibility_filter:
        query = (
            "Versions[?DeliveryOptions["
            f"?Visibility=='{visibility_filter}']].Sources[].Image"
        )
    else:
        query = "Versions[].Sources[].Image"

    ami_ids = jmespath.search(query, details)

    if ami_ids is None:
        return []
    return ami_ids
