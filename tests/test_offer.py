import json

from unittest.mock import Mock

from aws_mp_utils.offer import (
    create_update_offer_change_doc,
    get_ami_ids_in_mp_entity,
    get_available_dimensions,
    create_restrict_dimensions_offer_change_doc,
    create_add_dimensions_offer_change_doc
)


def test_create_update_offer_change_doc():
    expected = {
        'ChangeType': 'UpdateInformation',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': '123456789'
        }
    }

    details = {
        'Name': 'Offer name',
        'Description': 'Offer description',
        'PreExistingAgreement': {
            'AcquisitionChannel': 'External',
            'PricingModel': 'Byol'
        }
    }
    expected['Details'] = json.dumps(details)

    actual = create_update_offer_change_doc(
        '123456789',
        'Offer name',
        'Offer description',
        'External',
        'Byol'
    )
    assert expected == actual


def test_get_ami_ids_in_mp_entity():
    details = {
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
                        "SourceId": "1234",
                        "Visibility": "Public"
                    }
                ]
            },
            {
                "Sources": [
                    {
                        "Image": "ami-456",
                        "Id": "1233"
                    }
                ],
                "DeliveryOptions": [
                    {
                        "Id": "4322",
                        "SourceId": "1233",
                        "Visibility": "Restricted"
                    }
                ]
            },
            {
                "Sources": [
                    {
                        "Image": "ami-789",
                        "Id": "1232"
                    }
                ],
                "DeliveryOptions": [
                    {
                        "Id": "4323",
                        "SourceId": "1232",
                        "Visibility": "Public"
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

    ami_ids = get_ami_ids_in_mp_entity(
        client,
        '1234589',
        visibility_filter=''
    )
    assert ami_ids == ['ami-123', 'ami-456', 'ami-789']

    ami_ids = get_ami_ids_in_mp_entity(
        client,
        '1234589'
    )
    assert ami_ids == ['ami-123', 'ami-789']

    ami_ids = get_ami_ids_in_mp_entity(
        client,
        '1234589',
        visibility_filter='Restricted'
    )
    assert ami_ids == ['ami-456']


def test_get_available_dimensions():
    details = {
        "Dimensions": [
            {
                "Name": "u-3tb1.56xlarge",
                "Description": "u-3tb1.56xlarge",
                "Key": "u-3tb1.56xlarge",
                "Unit": "Hrs",
                "Types": ["Metered"]
            },
            {
                "Name": "t3.medium",
                "Description": "t3.medium",
                "Key": "t3.medium",
                "Unit": "Hrs",
                "Types": ["Metered"]
            }
        ]
    }

    entity = {
        'DetailsDocument': details
    }
    client = Mock()
    client.describe_entity.return_value = entity

    dimensions = get_available_dimensions(client, '1234589')
    assert len(dimensions) == 2
    assert dimensions[0]['Name'] == 't3.medium'
    assert dimensions[1]['Name'] == 'u-3tb1.56xlarge'

    # Test no dimensions found
    entity['DetailsDocument'] = {}
    dimensions = get_available_dimensions(client, '1234589')
    assert dimensions == []


def test_create_restrict_dimensions_offer_change_doc():
    expected = {
        'ChangeType': 'RestrictDimensions',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': '123456789'
        }
    }
    details = {
        'Restrictions': ['t2.micro', 't2.small']
    }
    expected['Details'] = json.dumps(details)

    actual = create_restrict_dimensions_offer_change_doc(
        offer_id='123456789',
        dimensions_to_restrict=['t2.micro', 't2.small']
    )
    assert expected == actual

    # Test with no dimensions
    details = {}
    expected['Details'] = json.dumps(details)
    actual = create_restrict_dimensions_offer_change_doc(offer_id='123456789')
    assert expected == actual


def test_create_add_dimensions_offer_change_doc():
    expected = {
        'ChangeType': 'AddDimensions',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': '123456789'
        }
    }
    details = [
        {
            'Key': 't2.micro',
            'Name': 't2.micro',
            'Description': 't2.micro',
            'Types': ['Metered'],
            'Unit': 'Hrs'
        }
    ]
    expected['Details'] = json.dumps(details)

    actual = create_add_dimensions_offer_change_doc(
        offer_id='123456789',
        dimensions_to_add=['t2.micro']
    )
    assert expected == actual

    # Test with no dimensions
    details = []
    expected['Details'] = json.dumps(details)
    actual = create_add_dimensions_offer_change_doc(offer_id='123456789')
    assert expected == actual
