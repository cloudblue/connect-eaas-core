import re
import subprocess
from collections import OrderedDict
from distutils.version import StrictVersion


DEFAULT_CLONE_DIR = '_repo'


class GitException(Exception):
    pass


def clone_repo(temp_path, repo_url):
    result = subprocess.run(
        [
            'git',
            '-C',
            temp_path,
            'clone',
            repo_url,
            DEFAULT_CLONE_DIR,
        ],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        result.check_returncode()
    except subprocess.CalledProcessError:
        raise GitException(f'Error cloning repository: {result.stderr.decode()}')


class ConnectVersionTag(StrictVersion):
    version_re = re.compile(
        r'^v?(\d+) \. (\d+) (\. (\d+))? ([ab](\d+))?$',
        re.VERBOSE | re.ASCII,
    )

    plain_tag = None

    def parse(self, vstring):
        try:
            super().parse(vstring)
        except Exception:
            self.plain_tag = vstring

    def _cmp_plain_tag(self, actual, other):
        if actual and other:
            if actual == other:
                return 0
            return -1 if actual > other else 1
        elif not actual and other:
            return 1
        if actual and not other:
            return -1
        return None

    def _cmp(self, other):
        result = self._cmp_plain_tag(self.plain_tag, other.plain_tag)
        if result is not None:
            return result

        return super()._cmp(other)


def sort_tags(tags):
    sorted_tags = OrderedDict()
    for tag in sorted(tags.keys(), key=ConnectVersionTag, reverse=True):
        sorted_tags[tag] = tags[tag]

    return sorted_tags


def list_tags(repo_url):
    result = subprocess.run(
        ['git', 'ls-remote', '--tags', '--refs', repo_url],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        result.check_returncode()
    except subprocess.CalledProcessError:
        raise GitException(result.stderr.decode())

    tags = {}
    for line in result.stdout.decode().splitlines():
        commit, tagref = line.split()
        tag = tagref.rsplit('/', 1)[-1]
        tags[tag] = commit
    return sort_tags(tags)
