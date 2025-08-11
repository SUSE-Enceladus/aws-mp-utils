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
import re
import time

import boto3
import botocore.exceptions as boto_exceptions

import jmespath

from aws_mp_utils.exceptions import AWSMPUtilsException


def get_change_set(client: boto3.client, change_set_id: str) -> dict:
    """
    Returns a dictionary containing changeset information
    The changeset is found based on the id.
    """
    response = client.describe_change_set(
        Catalog='AWSMarketplace',
        ChangeSetId=change_set_id
    )
    return response


def get_change_set_status(
    client: boto3.client,
    change_set_id: str
) -> str:
    """Gets the status of the changeset"""
    response = get_change_set(
        client,
        change_set_id
    )
    if response and 'Status' in response:
        # 'Status':'PREPARING'|'APPLYING'|'SUCCEEDED'|'CANCELLED'|'FAILED'
        status = response['Status'].lower()
        return status


def create_restrict_version_change_doc(
    entity_id: str,
    delivery_option_id: str
) -> dict:
    """
    Creates a restrict delivery option request dictionary.
    For use with submitting a changeset to delete an image
    or container version from a product.
    """
    data = {
        'ChangeType': 'RestrictDeliveryOptions',
        'Entity': {
            'Type': 'AmiProduct@1.0',
            'Identifier': entity_id
        }
    }
    details = {
        'DeliveryOptionIds': [delivery_option_id]
    }

    data['Details'] = json.dumps(details)
    return data


def create_add_version_change_doc(
    entity_id: str,
    version_title: str,
    ami_id: str,
    access_role_arn: str,
    release_notes: str,
    os_name: str,
    os_version: str,
    usage_instructions: str,
    recommended_instance_type: str,
    ssh_user: str = 'ec2-user',
    ingress_rules: list = None,
) -> dict:
    if not ingress_rules:
        ingress_rules = [{
            'FromPort': 22,
            'IpProtocol': 'tcp',
            'IpRanges': ['0.0.0.0/0'],
            'ToPort': 22
        }]

    data = {
        'ChangeType': 'AddDeliveryOptions',
        'Entity': {
            'Type': 'AmiProduct@1.0',
            'Identifier': entity_id
        }
    }

    details = {
        'Version': {
            'VersionTitle': version_title,
            'ReleaseNotes': release_notes
        },
        'DeliveryOptions': [{
            'Details': {
                'AmiDeliveryOptionDetails': {
                    'UsageInstructions': usage_instructions,
                    'RecommendedInstanceType': recommended_instance_type,
                    'AmiSource': {
                        'AmiId': ami_id,
                        'AccessRoleArn': access_role_arn,
                        'UserName': ssh_user,
                        'OperatingSystemName': os_name,
                        'OperatingSystemVersion': os_version
                    },
                    'SecurityGroups': ingress_rules
                }
            }
        }]
    }

    data['Details'] = json.dumps(details)
    return data


def start_mp_change_set(
    client: boto3.client,
    change_set: list,
    max_rechecks: int = 10,
    conflict_wait_period: int = 1800
) -> dict:
    """
    Additional params included in this function:
    - max_rechecks is the maximum number of checks that are
    performed when a marketplace change cannot be applied because some resource
    is affected by some other ongoing change (and ResourceInUseException is
    raised by boto3).
    - conflict_wait_period is the period (in seconds) that is waited
    between checks for the ongoing mp change to be finished (defaults to 900s).
    """
    retries = 3
    while retries > 0:
        conflicting_changeset = False
        conflicting_error_message = ''
        try:
            response = client.start_change_set(
                Catalog='AWSMarketplace',
                ChangeSet=change_set,
            )
            return response

        except boto_exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'ResourceInUseException':
                # Conflicting changeset for some resource
                conflicting_changeset = True
                conflicting_error_message = str(error)
            else:
                raise

        if conflicting_changeset:
            conflicting_changeset = False
            time.sleep(conflict_wait_period)
            max_rechecks -= 1
            if max_rechecks <= 0:
                try:
                    ongoing_change_id = get_ongoing_change_id_from_error(
                        conflicting_error_message
                    )
                    raise AWSMPUtilsException(
                        'Unable to complete successfully the mp change.'
                        f' Timed out waiting for {ongoing_change_id}'
                        ' to finish.'
                    )
                except Exception:
                    raise
        else:
            retries -= 1

    raise AWSMPUtilsException(
        'Unable to complete successfully the mp change.'
    )


def get_ongoing_change_id_from_error(message: str) -> str:
    re_change_id = r'change sets: (\w{25})'
    match = re.search(re_change_id, message)

    if match:
        change_id = match.group(1)
        return change_id
    else:
        raise AWSMPUtilsException(
            f'Unable to extract changeset id from aws err response: {message}'
        )


def get_image_delivery_option_id(
    client: boto3.client,
    entity_id: str,
    ami_id: str
) -> str:
    """
    Return delivery option id for image matching ami id in given offer
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
                        {
                            "Id": "4321",
                            "SourceId": "1234"
                        }
                    ]
                }
            ]
        }
    }
    """
    details = entity['DetailsDocument']

    source_id = jmespath.search(
        f"Versions[?Sources[?Image=='{ami_id}']] | [0].Sources | [0].Id",
        details
    )

    if not source_id:
        return None

    delivery_option_id = jmespath.search(
        f"Versions[?DeliveryOptions[?SourceId=='{source_id}']] | "
        "[0].DeliveryOptions | [0].Id",
        details
    )

    return delivery_option_id


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
    return [data]


def gen_update_delivery_options_changeset(
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
    override_parameters: list,
    delivery_option_id: str
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

    details = {
        'Version': {
            'VersionTitle': version_title,
            'ReleaseNotes': release_notes
        },
        'DeliveryOptions': [{
            'Id': delivery_option_id,
            'Details': {
                'HelmDeliveryOptionDetails': {
                    'DeliveryOptionTitle': delivery_option_title,
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
    return [data]
