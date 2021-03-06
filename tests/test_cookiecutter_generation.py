"""Test cookiecutter generation."""
from binaryornot.check import is_binary

import os
import pytest
import re
import sh
import subprocess
import sys


PATTERN = '{{(\s?cookiecutter)[.](.*?)}}'
RE_OBJ = re.compile(PATTERN)


@pytest.fixture
def context():
    """Cookiecutter context (variables) to be used."""
    return {
        'full_name': 'Websauna Team',
        'email': 'developers@websauna.org',
        'company': 'Websauna',
        'github_username': 'websauna',
        'project_name': 'Websauna: News portal',
        'project_short_description': 'Websauna news portal application.',
        'tags': 'python package websauna pyramid',
        'repo_name': 'websauna.application',
        'namespace': 'websauna',
        'package_name': 'application',
        'release_date': 'today',
        'year': '2017',
        'version': '1.0.0a1',
        'create_virtualenv': 'No',
        'authentication_random': '6c613c8193060d3738ca90103a6c79878150220b',
        'authomatic_random': 'dc999820aa1e1b71b166039f7f3cc8cee61567e0',
        'session_random': '42a8a98f766b8eba77a6326a579ecdf6d22b14b7',
    }


def build_files_list(root_dir):
    """Build a list containing absolute paths to the generated files."""
    return [
        os.path.join(dirpath, file_path)
        for dirpath, subdirs, files in os.walk(root_dir)
        for file_path in files
    ]


def check_paths(paths):
    """Check all paths have correct substitutions."""
    # Assert that no match is found in any of the files
    for path in paths:
        if is_binary(path) or ('/env/' in path):
            continue
        for line in open(path, 'r'):
            match = RE_OBJ.search(line)
            msg = 'cookiecutter variable not replaced in {0}'
            assert match is None, msg.format(path)


def test_invalid_package_name(cookies, context):
    """Pre_gen_project hook will fail if package_name is invalid."""
    context['repo_name'] = 'websauna.site'
    context['package_name'] = 'site'
    result = cookies.bake(extra_context=context)
    assert result.exit_code != 0
    assert result.exception is not None
    assert 'Hook script failed' in result.exception.args[0]


def test_generation(cookies, context):
    """Generated project should replace all variables."""
    result = cookies.bake(extra_context=context)
    assert result.exception is None
    assert result.exit_code == 0
    assert result.project.basename == context['repo_name']
    assert result.project.isdir()

    paths = build_files_list(str(result.project))
    assert paths
    check_paths(paths)


def test_code_qa(cookies, context):
    """Generated project should pass flake8 and py.test."""
    context['create_virtualenv'] = 'Yes'
    result = cookies.bake(extra_context=context)
    base_path = str(result.project)
    # Run Flake 8
    try:
        sh.flake8('{path}/setup.py {path}/{namespace}'.format(
                path=base_path,
                namespace=context['namespace']
            )
        )
    except sh.ErrorReturnCode as e:
        pytest.fail(e)
    # Run tests
    try:
        ls = sh.ls('{path}/env/bin/'.format(path=base_path))
        cmd = 'pytest'
        if 'pytest' in str(ls.stdout):
            cmd = './env/bin/pytest'
        proc = subprocess.Popen(
            [cmd],
            shell=sys.platform.startswith('win'),
            cwd=base_path
        )
        proc.wait()
    except Exception as e:
        print(ls.stdout)
        pytest.fail(e)
