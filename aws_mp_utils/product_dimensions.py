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

import json
import boto3
import jmespath


def get_product_details(
    client: boto3.client,
    product_id: str,
    catalog: str = 'AWSMarketplace'
) -> dict:
    """Fetch product entity document from AWS Marketplace Catalog API."""
    entity = client.describe_entity(
        Catalog=catalog,
        EntityId=product_id
    )
    details = entity['DetailsDocument']
    if isinstance(details, str):
        return json.loads(details)
    return details


def get_available_dimensions(
    client: boto3.client,
    product_id: str,
    catalog: str = 'AWSMarketplace'
) -> list[str]:
    """Lists the available dimensions for the given product."""
    details = get_product_details(
        client=client,
        product_id=product_id,
        catalog=catalog
    )

    query = "Dimensions"
    dimensions = jmespath.search(query, details)

    if dimensions is None:
        return []
    return sorted(dimensions, key=lambda x: x['Name'])


def create_restrict_dimensions_change_doc(
    product_id: str,
    details_document: str,
    entity_type: str = 'Product@1.0',
) -> dict:
    """Creates an update product request dictionary to restrict dimensions.

    :param product_id: The unique identifier of product in AWS Marketplace.
    :param details_document: A JSON formatted string containing details doc.
    :param entity_type: Product entity type (e.g. Product@1.0, SaaSProduct@1.0
        or ContainerProduct@1.0).
    """
    data = {
        'ChangeType': "RestrictDimensions",
        'Entity': {
            'Type': entity_type,
            'Identifier': product_id
        },
        'DetailsDocument': json.loads(details_document)
    }
    return data


def create_add_dimensions_change_doc(
    product_id: str,
    details_document: str,
    entity_type: str = 'Product@1.0',
) -> dict:
    """Creates an update product request dictionary to add dimensions."""
    data = {
        'ChangeType': "AddDimensions",
        'Entity': {
            'Type': entity_type,
            'Identifier': product_id
        },
        'DetailsDocument': json.loads(details_document)
    }
    return data
