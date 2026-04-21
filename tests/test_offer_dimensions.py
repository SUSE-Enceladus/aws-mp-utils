from unittest.mock import Mock

from aws_mp_utils.offer_dimensions import (
    get_available_dimensions,
    create_restrict_dimensions_change_doc,
    create_add_dimensions_change_doc
)


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


def test_create_restrict_dimensions_change_doc():
    details_doc = '{"Restrictions": ["t2.micro", "t2.small"]}'
    expected = {
        'ChangeType': 'RestrictDimensions',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': '123456789'
        },
        'DetailsDocument': details_doc
    }

    actual = create_restrict_dimensions_change_doc(
        offer_id='123456789',
        details_document=details_doc
    )
    assert expected == actual


def test_create_add_dimensions_change_doc():
    details_doc = '[{"Key": "t2.micro", "Name": "t2.micro"}]'
    expected = {
        'ChangeType': 'AddDimensions',
        'Entity': {
            'Type': 'Offer@1.0',
            'Identifier': '123456789'
        },
        'DetailsDocument': details_doc
    }

    actual = create_add_dimensions_change_doc(
        offer_id='123456789',
        details_document=details_doc
    )
    assert expected == actual
