import json

from aws_mp_utils.offer import create_update_offer_change_doc


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
