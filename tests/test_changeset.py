from unittest.mock import Mock

from aws_mp_utils.changeset import get_change_set


def test_get_change_set():
    response = {
        'ChangeSetId': '123',
        'ChangeSetArn': 'string',
        'ChangeSetName': 'string',
        'Intent': 'APPLY',
        'StartTime': '2018-02-27T13:45:22Z',
        'EndTime': '2018-02-27T13:45:22Z',
        'Status': 'SUCCEEDED',
        'ChangeSet': [
            {
                'ChangeType': 'string',
                'Entity': {
                    'Type': 'string',
                    'Identifier': 'string'
                },
                'Details': 'string',
                'DetailsDocument': {'changeset': 'details'},
                'ChangeName': 'string'
            },
        ]
    }

    client = Mock()
    client.describe_change_set.return_value = response

    response = get_change_set(client, '123')
    assert response['ChangeSetId'] == '123'
