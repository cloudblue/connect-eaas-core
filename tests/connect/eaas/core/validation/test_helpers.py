from connect.eaas.core.validation.helpers import get_code_context


def test_get_code_context_module(mocker):
    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.getsourcefile',
        return_value='path/file.py',
    )

    pattern = 'target_pattern'
    pattern_line = 6
    code_lines = [f'line {i}\n' for i in range(10)]
    code_lines[pattern_line] = f'something {pattern} something\n'

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

    result = get_code_context(mocker.MagicMock(), pattern)

    expected_lineno = 1 + pattern_line
    assert result['file'] == 'path/file.py'
    assert result['start_line'] == 1
    assert result['lineno'] == expected_lineno
    assert result['code'] == ''.join(code_lines[0:expected_lineno + 3])


def test_get_code_context_function(mocker):
    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.getsourcefile',
        return_value='path/file.py',
    )

    pattern = 'target_pattern'
    pattern_line = 6
    code_lines = [f'line {i}\n' for i in range(10)]
    code_lines[pattern_line] = f'something {pattern} something\n'

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

    result = get_code_context(mocker.MagicMock(), pattern)

    assert result['file'] == 'path/file.py'
    assert result['start_line'] == 1
    assert result['lineno'] == 1 + pattern_line
    assert result['code'] == ''.join(code_lines)


def test_get_code_context_pattern_not_found(mocker):
    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.getsourcefile',
        return_value='path/file.py',
    )

    code_lines = [f'line {i}\n' for i in range(10)]

    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.getsourcelines',
        return_value=(
            code_lines,
            5,
        ),
    )
    mocker.patch(
        'connect.eaas.core.validation.helpers.inspect.ismodule',
        return_value=False,
    )

    result = get_code_context(mocker.MagicMock(), 'nonexistent_pattern')

    assert result['file'] == 'path/file.py'
    assert result['start_line'] == 5
    assert result['lineno'] == 5
    assert result['code'] == ''.join(code_lines)
