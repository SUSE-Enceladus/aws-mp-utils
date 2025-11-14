import json

from unittest.mock import Mock

from aws_mp_utils.image import (
    create_restrict_version_change_doc,
    get_image_delivery_option_id,
    get_images_details
)


def test_create_restrict_version_change_doc():
    expected = {
        'ChangeType': 'RestrictDeliveryOptions',
        'Entity': {
            'Type': 'AmiProduct@1.0',
            'Identifier': '123456789'
        }
    }
    details = {
        'DeliveryOptionIds': ['987654321']
    }
    expected['Details'] = json.dumps(details)

    actual = create_restrict_version_change_doc('123456789', '987654321')
    assert expected == actual


def test_get_image_delivery_option_id():
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
            }
        ]
    }

    entity = {
        'DetailsDocument': details
    }
    client = Mock()
    client.describe_entity.return_value = entity

    did = get_image_delivery_option_id(
        client,
        '1234589',
        'ami-123',
    )
    assert did == '4321'

    # Test no image match found
    details['Versions'][0]['Sources'][0]['Image'] = 'ami-321'
    entity['Details'] = json.dumps(details)

    did = get_image_delivery_option_id(
        client,
        '1234589',
        'ami-123',
    )
    assert did is None


def test_get_images_details():
    expected_images = [
        {
          'Name': 'image_1',
            'State': 'active',
            'OwnerId': '12345'
        },
        {
            'Name': 'image_2',
            'State': 'inactive',
            'OwnerId': '54321'
        }
    ]
    describe_images_response = {
        'Images': expected_images
    }
    client = Mock()
    client.describe_images.return_value = describe_images_response
    ami_ids = ['ami-12345', 'ami-67890']
    images = get_images_details(client=client, ami_ids=ami_ids)
    assert images == expected_images
    client.describe_images.assert_called_once_with(ImageIds=ami_ids)
