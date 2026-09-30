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


def get_available_regions(
    client: boto3.client,
    product_id: str,
    catalog: str = 'AWSMarketplace'
) -> dict:
    """Lists available regions and region availability details for product."""
    details = get_product_details(
        client=client,
        product_id=product_id,
        catalog=catalog
    )

    region_availability = jmespath.search("RegionAvailability", details)
    if isinstance(region_availability, dict):
        regions = region_availability.get("Regions")
        if isinstance(regions, list):
            region_availability["Regions"] = sorted(list(set(regions)))
        return region_availability

    query_regions = "Regions"
    regions = jmespath.search(query_regions, details)

    if regions is None:
        regions_list = []
    else:
        regions_list = sorted(list(set(regions)))

    query_future = "FutureRegionSupport"
    future_support = jmespath.search(query_future, details)

    res = {'Regions': regions_list}
    if future_support is not None:
        res['FutureRegionSupport'] = future_support
    return res


def create_restrict_regions_change_doc(
    product_id: str,
    regions: list[str],
    entity_type: str = 'AmiProduct@1.0',
) -> dict:
    """Creates an update product request dict to restrict regions.

    :param product_id: The unique identifier of product in AWS Marketplace.
    :param regions: A list of regions for restriction in the product.
    :param entity_type: Product entity type (e.g. AmiProduct@1.0,
        SaaSProduct@1.0, ContainerProduct@1.0 or Product@1.0).
    """
    data = {
        'ChangeType': "RestrictRegions",
        'Entity': {
            'Type': entity_type,
            'Identifier': product_id
        },
        'DetailsDocument': {
            'Regions': regions
        }
    }
    return data


def create_add_regions_change_doc(
    product_id: str,
    regions: list[str],
    entity_type: str = 'AmiProduct@1.0',
) -> dict:
    """Creates an update product request dict to add regions.

    :param product_id: The unique identifier of product in AWS Marketplace.
    :param regions: A list of regions for addition in the product.
    :param entity_type: Product entity type (e.g. AmiProduct@1.0,
        SaaSProduct@1.0, ContainerProduct@1.0 or Product@1.0).
    """
    data = {
        'ChangeType': "AddRegions",
        'Entity': {
            'Type': entity_type,
            'Identifier': product_id
        },
        'DetailsDocument': {
            'Regions': regions
        }
    }
    return data
