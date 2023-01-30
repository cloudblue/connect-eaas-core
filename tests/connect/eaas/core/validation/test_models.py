from connect.eaas.core.validation.models import ValidationItem, ValidationResult


def test_validation_res_to_dict():
    item1 = ValidationItem(
        message='some error',
        file='extension.py',
        start_line='123',
        lineno=1,
        code='def fix_me(self)',
    )
    item2 = ValidationItem(
        level='ERROR',
        message='big error',
        file='extension.py',
    )
    res = ValidationResult(
        items=[item1, item2],
        must_exit=True,
        context={'ext_class': 'MyAwesomeExtension'},
    )

    assert isinstance(res, ValidationResult)
    assert isinstance(item1, ValidationItem)
    assert isinstance(item2, ValidationItem)
    dict_res = res.dict()

    assert dict_res['must_exit'] is True
    assert dict_res['context'] == {'ext_class': 'MyAwesomeExtension'}
    assert len(dict_res['items']) == 2
    print(dict_res['items'])
    assert {
        'level': 'WARNING',
        'message': 'some error',
        'file': 'extension.py',
        'start_line': 123,
        'lineno': 1,
        'code': 'def fix_me(self)',
    } in dict_res['items']
    assert {
        'level': 'ERROR',
        'message': 'big error',
        'file': 'extension.py',
        'start_line': None,
        'lineno': None,
        'code': None,
    } in dict_res['items']
