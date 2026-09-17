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


def get_available_instance_types(
    client: boto3.client,
    product_id: str,
    catalog: str = 'AWSMarketplace'
) -> list[str]:
    """Lists the available instance types for the given product."""
    details = get_product_details(
        client=client,
        product_id=product_id,
        catalog=catalog
    )

    query = "Compatibility.AvailableInstanceTypes"
    instance_types = jmespath.search(query, details)

    if instance_types is None:
        return []
    return sorted(list(set(instance_types)))


def create_restrict_instance_types_change_doc(
    product_id: str,
    instance_types: list[str],
    entity_type: str = 'Product@1.0',
) -> dict:
    """Creates an update product request dict to restrict instance types.

    :param product_id: The unique identifier of product in AWS Marketplace.
    :param instance_types: A list of instance types for restriction in the
        product.
    :param entity_type: Product entity type (e.g. Product@1.0,
        SaaSProduct@1.0, ContainerProduct@1.0 or AmiProduct@1.0).
    """
    data = {
        'ChangeType': "RestrictInstanceTypes",
        'Entity': {
            'Type': entity_type,
            'Identifier': product_id
        },
        'DetailsDocument': {
            'InstanceTypes': instance_types
        }
    }
    return data


def create_add_instance_types_change_doc(
    product_id: str,
    instance_types: list[str],
    entity_type: str = 'Product@1.0',
) -> dict:
    """Creates an update product request dict to add instance types.

    :param product_id: The unique identifier of product in AWS Marketplace.
    :param instance_types: A list of instance types for addition in the
        product.
    :param entity_type: Product entity type (e.g. Product@1.0,
        SaaSProduct@1.0, ContainerProduct@1.0 or AmiProduct@1.0).
    """
    data = {
        'ChangeType': "AddInstanceTypes",
        'Entity': {
            'Type': entity_type,
            'Identifier': product_id
        },
        'DetailsDocument': {
            'InstanceTypes': instance_types
        }
    }
    return data
