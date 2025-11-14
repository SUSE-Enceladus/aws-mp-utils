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


def get_images_details(
    client: boto3.client,
    ami_ids: list[str]
) -> dict:
    """
    Returns the details for the ami-ids provided.
    """
    response = client.describe_images(
        ImageIds=ami_ids
    )

    return response.get('Images', [])
