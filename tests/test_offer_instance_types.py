from unittest.mock import Mock

from aws_mp_utils.offer_instance_types import (
    get_available_instance_types,
    create_restrict_instance_types_change_doc,
    create_add_instance_types_change_doc
)


def test_get_available_instance_types():
    details = {
        "Versions": [
            {
                "Sources": [
                    {
                        "Compatibility": {
                            "AvailableInstanceTypes": [
                                "u-3tb1.56xlarge",
                                "t3.medium",
                                "t3.medium"
                            ]
                        }
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

    instance_types = get_available_instance_types(client, '1234589')
    assert len(instance_types) == 2
    assert instance_types[0] == 't3.medium'
    assert instance_types[1] == 'u-3tb1.56xlarge'

    # Test no instance types found
    entity['DetailsDocument'] = {}
    instance_types = get_available_instance_types(client, '1234589')
    assert instance_types == []


def test_create_restrict_instance_types_change_doc():
    instance_types = ['t2.micro', 't2.small']
    expected = {
        'ChangeType': 'RestrictInstanceTypes',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': '123456789'
        },
        'DetailsDocument': {
            'InstanceTypes': ['t2.micro', 't2.small']
        }
    }

    actual = create_restrict_instance_types_change_doc(
        offer_id='123456789',
        instance_types=instance_types
    )
    assert expected == actual


def test_create_add_instance_types_change_doc():
    instance_types = ['t2.micro', 't2.small']
    expected = {
        'ChangeType': 'AddInstanceTypes',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': '123456789'
        },
        'DetailsDocument': {
            'InstanceTypes': ['t2.micro', 't2.small']
        }
    }

    actual = create_add_instance_types_change_doc(
        offer_id='123456789',
        instance_types=instance_types
    )
    assert expected == actual
