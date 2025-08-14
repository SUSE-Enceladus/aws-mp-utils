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


def get_helm_delivery_option_id(
    client: boto3.client,
    entity_id: str,
    version_title: str
) -> str:
    """
    Provides the id of the delivery option to be updated. The id of
    the delivery option is selected from the version of the product
    that matches the version_title provided. The delivery option is
    the first delivery option of the type 'Helm' in that version.
    Example describe entity output:
    {
        "Details": {
            "Versions": [
                {
                    "VersionTitle": "Product 1.2.3",
                    "DeliveryOptions": [
                        {
                            "Id": "4321",
                            "Type": "Helm"
                        }
                    ]
                }
            ]
        }
    }
    """
    entity = client.describe_entity(
        Catalog='AWSMarketplace',
        EntityId=entity_id
    )
    details = entity['DetailsDocument']

    result = jmespath.search(
        f"Versions[?VersionTitle=='{version_title}'] | [0]"
        ".DeliveryOptions[?Type=='Helm'] | [0].Id",
        details
    )
    return result


def gen_add_delivery_options_changeset(
    entity_id: str,
    version_title: str,
    release_notes: str,
    delivery_option_title: str,
    compatible_services: list,
    container_images: list,
    helm_chart_uri: str,
    helm_chart_description: str,
    usage_instructions: str,
    quick_launch_enabled: bool,
    marketplace_service_account_name: str,
    release_name: str,
    namespace: str,
    override_parameters: list
) -> dict:
    """
    Function to generate a marketplace changeset of AddDeliveryOptions type
    https://docs.aws.amazon.com/marketplace-catalog/latest/api-reference/
    container-products.html#working-with-container-products
    """

    data = {
        'ChangeType': 'AddDeliveryOptions',
        'Entity': {
            'Type': 'ContainerProduct@1.0',
            'Identifier': entity_id
        }
    }

    details = {
        'Version': {
            'VersionTitle': version_title,
            'ReleaseNotes': release_notes
        },
        'DeliveryOptions': [{
            'DeliveryOptionTitle': delivery_option_title,
            'Details': {
                'HelmDeliveryOptionDetails': {
                    'CompatibleServices': compatible_services,
                    'ContainerImages': container_images,
                    'HelmChartUri': helm_chart_uri,
                    'Description': helm_chart_description,
                    'UsageInstructions': usage_instructions,
                    'QuickLaunchEnabled': quick_launch_enabled,
                    'MarketplaceServiceAccountName':
                        marketplace_service_account_name,
                    'ReleaseName': release_name,
                    'Namespace': namespace,
                    'OverrideParameters': override_parameters
                }
            }
        }]
    }

    data['Details'] = json.dumps(details)
    return data


def gen_update_delivery_options_changeset(
    entity_id: str,
    delivery_option_id: str,
    version_title: str = None,
    release_notes: str = None,
    delivery_option_title: str = None,
    compatible_services: list = None,
    container_images: list = None,
    helm_chart_uri: str = None,
    helm_chart_description: str = None,
    usage_instructions: str = None,
    quick_launch_enabled: bool = None,
    marketplace_service_account_name: str = None,
    release_name: str = None,
    namespace: str = None,
    override_parameters: list = None
) -> dict:
    """
    Function to generate a marketplace changeset of UpdateDeliveryOptions
    type https://docs.aws.amazon.com/marketplace-catalog/latest/
    api-reference/container-products.html#working-with-container-products
    """

    data = {
        'ChangeType': 'UpdateDeliveryOptions',
        'Entity': {
            'Type': 'ContainerProduct@1.0',
            'Identifier': entity_id
        }
    }

    version = {}
    helm_details = {}
    details = {}

    if version_title:
        version['VersionTitle'] = version_title

    if release_notes:
        version['ReleaseNotes'] = release_notes

    if version:
        details['Version'] = version

    if delivery_option_title:
        helm_details['DeliveryOptionTitle'] = delivery_option_title

    if compatible_services:
        helm_details['CompatibleServices'] = compatible_services

    if container_images:
        helm_details['ContainerImages'] = container_images

    if helm_chart_uri:
        helm_details['HelmChartUri'] = helm_chart_uri

    if helm_chart_description:
        helm_details['Description'] = helm_chart_description

    if usage_instructions:
        helm_details['UsageInstructions'] = usage_instructions

    if quick_launch_enabled is not None:
        helm_details['QuickLaunchEnabled'] = quick_launch_enabled

    if marketplace_service_account_name:
        helm_details['MarketplaceServiceAccountName'] = \
            marketplace_service_account_name

    if release_name:
        helm_details['ReleaseName'] = release_name

    if namespace:
        helm_details['Namespace'] = namespace

    if override_parameters:
        helm_details['OverrideParameters'] = override_parameters

    if helm_details:
        details['DeliveryOptions'] = [
            {
                'Id': delivery_option_id,
                'Details': {
                    'HelmDeliveryOptionDetails': helm_details
                }
            }
        ]

    data['Details'] = json.dumps(details)
    return data
