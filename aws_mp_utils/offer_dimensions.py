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


def get_available_dimensions(
    client: boto3.client,
    offer_id: str,
    catalog: str = 'AWSMarketplace'
) -> list[str]:
    """
    Lists the available dimensions for the given offer.
    """
    entity = client.describe_entity(
        Catalog=catalog,
        EntityId=offer_id
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
                        },
                        "Compatibility": {
                            "AvailableInstanceTypes": [
                                ...
                            ]
                    ],
                }
            ],
            "Dimensions": [
                {
                    "Name": "u-3tb1.56xlarge",
                    "Description": "u-3tb1.56xlarge",
                    "Key": "u-3tb1.56xlarge",
                    "Unit": "Hrs",
                    "Types": [
                        "Metered"
                    ]
                },
                ...
            ]
        }
    }
    """

    details = entity['DetailsDocument']
    query = "Dimensions"
    dimensions = jmespath.search(query, details)

    if dimensions is None:
        return []
    return sorted(dimensions, key=lambda x: x['Name'])


def create_restrict_dimensions_change_doc(
    offer_id: str,
    details_document: str,
) -> dict:
    """
    Creates an update offer request dictionary to restrict dimensions.

    :param offer_id: The unique identifier of the offer in the AWS Marketplace.
    :param details_document: A JSON formatted string containing the details
        document for restricting the offer dimensions.
    """
    data = {
        'ChangeType': "RestrictDimensions",
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': offer_id
        },
        'DetailsDocument': details_document
    }
    return data


def create_add_dimensions_change_doc(
    offer_id: str,
    details_document: str,
) -> dict:
    """
    Creates an update offer request dictionary to add dimensions.
    """

    data = {
        'ChangeType': "AddDimensions",
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': offer_id
        },
        'DetailsDocument': details_document
    }
    return data
