import json

from unittest.mock import Mock

from aws_mp_utils.offer import (
    create_update_offer_change_doc,
    get_ami_ids_in_mp_entity
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
                        "SourceId": "1234"
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
                        "SourceId": "1233"
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
                        "SourceId": "1232"
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
        '1234589'
    )
    assert ami_ids == ['ami-123', 'ami-456', 'ami-789']
