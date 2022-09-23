from connect.eaas.core.validation.helpers import get_code_context


def test_get_code_context_module(mocker, faker):
    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.getsourcefile',
        return_value='path/file.py',
    )

    code_lines = [f'{line}\n' for line in faker.paragraphs(nb=10)]

    code = ''.join(code_lines)

    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.getsourcelines',
        return_value=(
            code_lines,
            1,
        ),
    )
    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.ismodule',
        return_value=True,
    )

    result = get_code_context(mocker.MagicMock(), 'country store build before')

    assert result['file'] == 'path/file.py'
    assert result['start_line'] == 1
    assert result['lineno'] == 7
    assert result['code'] == ''.join(code.splitlines(keepends=True)[0:7 + 3])


def test_get_code_context_function(mocker, faker):
    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.getsourcefile',
        return_value='path/file.py',
    )

    code_lines = [f'{line}\n' for line in faker.paragraphs(nb=10)]

    code = ''.join(code_lines)

    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.getsourcelines',
        return_value=(
            code_lines,
            1,
        ),
    )
    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.ismodule',
        return_value=False,
    )

    result = get_code_context(mocker.MagicMock(), 'country store build before')

    assert result['file'] == 'path/file.py'
    assert result['start_line'] == 1
    assert result['lineno'] == 7
    assert result['code'] == ''.join(code.splitlines(keepends=True))
