import subprocess

import pytest

from connect.eaas.core.deployment.helpers import (
    DEFAULT_CLONE_DIR,
    GitException,
    clone_repo,
    list_tags,
)


_DEFAULT_SUBP_KWARGS = {
    'capture_output': True,
    'stdin': subprocess.DEVNULL,
    'start_new_session': True,
}


def test_clone_ok(mocker):
    result = mocker.MagicMock()
    result.returnvalue = 0
    temp_path = '/tmp/tests'
    repo_url = 'https://github.com/dummy/repo.git'
    cmd = [
        'git',
        '-C',
        temp_path,
        'clone',
        '-b',
        '1.0',
        repo_url,
        DEFAULT_CLONE_DIR,
    ]
    subp_mock = mocker.patch(
        'connect.eaas.core.deployment.helpers.subprocess.run',
        return_value=result,
    )

    clone_repo(temp_path, repo_url, '1.0')
    subp_mock.assert_called_once_with(cmd, **_DEFAULT_SUBP_KWARGS)


def test_clone_repo_subprocess_failed(mocker):
    result = mocker.MagicMock()
    result.check_returncode = mocker.MagicMock(
        side_effect=subprocess.CalledProcessError(128, cmd=[]),
    )
    error = 'error message'
    result.stderr = error.encode('utf-8')
    mocker.patch(
        'connect.eaas.core.deployment.helpers.subprocess.run',
        return_value=result,
    )

    with pytest.raises(GitException) as cv:
        clone_repo('/tmp/tests', 'https://github.com/dummy/repo.git', '1.0')

    assert str(cv.value) == f'Error cloning repository https://github.com/dummy/repo.git: {error}'


def test_list_tags_ok(mocker):
    commit_id = '0c92d254606ad06c2669dd29a65a28b577cf3b1e'
    tag_id = '21.7'
    result = mocker.MagicMock()
    result.returnvalue = 0
    result.stdout = f'{commit_id}        refs/tags/{tag_id}\n'.encode('utf-8')
    subp_mock = mocker.patch(
        'connect.eaas.core.deployment.helpers.subprocess.run',
        return_value=result,
    )
    data = list_tags('https://github.com/dummy/repo.git')
    subp_mock.assert_called_once_with(
        [
            'git',
            'ls-remote',
            '--tags',
            '--refs',
            'https://github.com/dummy/repo.git',
        ],
        **_DEFAULT_SUBP_KWARGS,
    )
    assert isinstance(data, dict)
    assert len(data) == 1
    assert tag_id in data
    assert data[tag_id] == commit_id


def test_list_tags_ordering(mocker):
    commit = '0c92d254606ad06c2669dd29a65a28b577cf3b1e'
    tag_1 = '21.7'
    tag_2 = '12.7-d'
    tag_3 = 'v21.8'
    tag_4 = 'fresco'
    tag_5 = 'v1.2.3'
    tag_6 = 'alfa'
    result = mocker.MagicMock()
    result.returnvalue = 0
    res_stdout = f'{commit}        refs/tags/{tag_1}\n{commit}        refs/tags/{tag_2}\n'
    res_stdout += f'{commit}        refs/tags/{tag_3}\n{commit}        refs/tags/{tag_4}\n'
    res_stdout += f'{commit}        refs/tags/{tag_5}\n{commit}        refs/tags/{tag_6}\n'
    result.stdout = res_stdout.encode('utf-8')
    mocker.patch(
        'connect.eaas.core.deployment.helpers.subprocess.run',
        return_value=result,
    )
    data = list_tags('https://github.com/dummy/repo.git')
    assert list(data.keys()) == [tag_3, tag_1, tag_5, tag_2, tag_6, tag_4]


def test_list_tags_duplicated_tags(mocker):
    commit_1 = '0c92d254606ad06c2669dd29a65a28b577cf3b1e'
    commit_2 = '0c92d254606ad06c2669dd29a65a28b577cf3b11'
    tag_id = '21.7'
    result = mocker.MagicMock()
    result.returnvalue = 0
    res_stdout = f'{commit_1}        refs/tags/{tag_id}\n{commit_2}        refs/tags/{tag_id}\n'
    result.stdout = res_stdout.encode('utf-8')
    mocker.patch(
        'connect.eaas.core.deployment.helpers.subprocess.run',
        return_value=result,
    )
    data = list_tags('https://github.com/dummy/repo.git')
    assert isinstance(data, dict)
    assert len(data) == 1
    assert tag_id in data
    assert data[tag_id] == commit_2


def test_list_tags_impossible_values_ok(mocker):
    commit = '0c92d254606ad06c2669dd29a65a28b577cf3b1e'
    tag_1 = -1
    tag_2 = 'fdfs!123@'
    result = mocker.MagicMock()
    result.returnvalue = 0
    res_stdout = f'{commit}        refs/tags/{tag_1}\n{commit}        refs/tags/{tag_2}\n'
    result.stdout = res_stdout.encode('utf-8')
    mocker.patch(
        'connect.eaas.core.deployment.helpers.subprocess.run',
        return_value=result,
    )
    data = list_tags('https://github.com/dummy/repo.git')
    assert list(data.keys()) == [str(tag_1), tag_2]


def test_list_tags_subprocess_failed(mocker):
    result = mocker.MagicMock()
    result.check_returncode = mocker.MagicMock(
        side_effect=subprocess.CalledProcessError(128, cmd=[]),
    )
    error = 'error message'
    result.stderr = error.encode('utf-8')
    mocker.patch(
        'connect.eaas.core.deployment.helpers.subprocess.run',
        return_value=result,
    )

    with pytest.raises(GitException) as cv:
        list_tags('https://github.com/dummy/repo.git')

    assert str(cv.value) == error
