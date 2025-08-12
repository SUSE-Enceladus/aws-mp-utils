
import json

from unittest.mock import Mock

from aws_mp_utils.container import (
    get_helm_delivery_option_id,
    gen_add_delivery_options_changeset,
    gen_update_delivery_options_changeset
)


def test_get_helm_delivery_option_id():
    details = {
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

    entity = {
        'DetailsDocument': details
    }
    client = Mock()
    client.describe_entity.return_value = entity

    did = get_helm_delivery_option_id(
        client,
        '1234589',
        'Product 1.2.3',
    )
    assert did == '4321'

    # Test no image match found
    details['Versions'][0]['VersionTitle'] = 'Product 1.2.4'
    entity['Details'] = json.dumps(details)

    did = get_helm_delivery_option_id(
        client,
        '1234589',
        'Product 1.2.3',
    )
    assert did is None


def test_gen_add_delivery_options_changeset():
    response = gen_add_delivery_options_changeset(
        '123',
        'Chart 1.2.3',
        'Release Notes...',
        'Chart - 1.2.3',
        ['EKS'],
        ['123.dkr.ecr.us-east-1.amazonaws.com/sellername/reponame1:1'],
        '123.dkr.ecr.us-east-1.amazonaws.com/sellername/reponame1:helmchart1',
        'Helm chart description',
        'Usage instructions',
        True,
        'Service account name',
        'Optional release name',
        'Optional k8s namespace',
        [
            {
                "Key": "HelmKeyName1",
                "DefaultValue": "${AWSMP_LICENSE_SECRET}",
                "Metadata":
                {
                    "Label": "AWS CloudFormation template field label",
                    "Description": "AWS CloudFormation field description",
                    "Obfuscate": False
                }
            }
        ]
    )
    assert 'Details' in response
    assert response['ChangeType'] == 'AddDeliveryOptions'


def test_gen_update_delivery_options_changeset():
    response = gen_update_delivery_options_changeset(
        '123',
        'Chart 1.2.3',
        'Release Notes...',
        'Chart - 1.2.3',
        ['EKS'],
        ['123.dkr.ecr.us-east-1.amazonaws.com/sellername/reponame1:1'],
        '123.dkr.ecr.us-east-1.amazonaws.com/sellername/reponame1:helmchart1',
        'Helm chart description',
        'Usage instructions',
        True,
        'Service account name',
        'Optional release name',
        'Optional k8s namespace',
        [
            {
                "Key": "HelmKeyName1",
                "DefaultValue": "${AWSMP_LICENSE_SECRET}",
                "Metadata":
                {
                    "Label": "AWS CloudFormation template field label",
                    "Description": "AWS CloudFormation field description",
                    "Obfuscate": False
                }
            }
        ],
        '123-321'
    )
    assert 'Details' in response
    assert response['ChangeType'] == 'UpdateDeliveryOptions'
