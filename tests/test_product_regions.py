from unittest.mock import Mock

from aws_mp_utils.product_regions import (
    get_available_regions,
    create_restrict_regions_change_doc,
    create_add_regions_change_doc
)


def test_get_available_regions():
    details = {
        "RegionAvailability": {
            "Regions": [
                "us-west-2",
                "us-east-1",
                "us-east-1"
            ],
            "FutureRegionSupport": {
                "SupportedRegions": ["All"]
            }
        }
    }

    entity = {
        'DetailsDocument': details
    }
    client = Mock()
    client.describe_entity.return_value = entity

    regions_data = get_available_regions(client, '1234589')
    assert len(regions_data['Regions']) == 2
    assert regions_data['Regions'][0] == 'us-east-1'
    assert regions_data['Regions'][1] == 'us-west-2'
    expected_future = {"SupportedRegions": ["All"]}
    assert regions_data['FutureRegionSupport'] == expected_future

    # Test fallback to Regions top-level key
    entity['DetailsDocument'] = {
        "Regions": ["us-east-1", "eu-central-1"]
    }
    regions_data = get_available_regions(client, '1234589')
    assert len(regions_data['Regions']) == 2
    assert regions_data['Regions'][0] == 'eu-central-1'
    assert regions_data['Regions'][1] == 'us-east-1'

    # Test no regions found
    entity['DetailsDocument'] = {}
    regions_data = get_available_regions(client, '1234589')
    assert regions_data['Regions'] == []


def test_create_restrict_regions_change_doc():
    regions = ['us-east-1', 'us-west-2']
    expected = {
        'ChangeType': 'RestrictRegions',
        'Entity': {
            'Type': 'AmiProduct@1.0',
            'Identifier': '123456789'
        },
        'DetailsDocument': {
            'Regions': ['us-east-1', 'us-west-2']
        }
    }

    actual = create_restrict_regions_change_doc(
        product_id='123456789',
        regions=regions
    )
    assert expected == actual


def test_create_add_regions_change_doc():
    regions = ['us-east-1', 'us-west-2']
    expected = {
        'ChangeType': 'AddRegions',
        'Entity': {
            'Type': 'AmiProduct@1.0',
            'Identifier': '123456789'
        },
        'DetailsDocument': {
            'Regions': ['us-east-1', 'us-west-2']
        }
    }

    actual = create_add_regions_change_doc(
        product_id='123456789',
        regions=regions
    )
    assert expected == actual
