import os
import re

import pytest
from binaryornot.check import is_binary


@pytest.fixture
def context():
    return {
        "ansible_project_name": "store ansible",
        "ansible_project_slug": "store_ansible",
        "application_name": "store",
        "application_slug": "store",
        "application_user": "hack",
        "application_root": "/hack/store",
        "add_your_pulic_key": "n",
        "add_letsencrypt_certificate": "y",
    }


def build_files_list(root_dir):
    """Build a list containing absolute paths to the generated files."""
    return [
        os.path.join(dirpath, file_path)
        for dirpath, subdirs, files in os.walk(root_dir)
        for file_path in files
    ]


def check_substitutions(paths):
    """Method to check all paths have correct substitutions,
    used by other tests cases
    """
    # Assert that no match is found in any of the files

    PATTERN = '{{(\s?cookiecutter)[.](.*?)}}'
    RE_OBJ = re.compile(PATTERN)

    for path in paths:
        if is_binary(path):
            continue
        for line in open(path, 'r'):
            match = RE_OBJ.search(line)
            msg = 'cookiecutter variable not replaced in {}'
            assert match is None, msg.format(path)


def test_default_configuration(cookies, context):
    result = cookies.bake(extra_context=context)
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project.basename == context['ansible_project_slug']
    assert result.project.isdir()

    paths = build_files_list(str(result.project))
    assert paths
    check_substitutions(paths)


def check_password_replaced(paths):
    PATTERN = 'POSTGRES_PASSWORD!!!'
    RE_OBJ = re.compile(PATTERN)

    for path in paths:
        if not is_binary(path):
            for line in open(path, 'r'):
                match = RE_OBJ.search(line)
                msg = 'password variable not replaced in {}'
                assert match is None, msg.format(path)


def test_postgres_password_hook(cookies, context):
    result = cookies.bake(extra_context=context)

    assert result.exit_code == 0

    paths = build_files_list(str(result.project))
    assert paths
    check_password_replaced(paths)


@pytest.mark.skipif('TRAVIS' in os.environ,
                    reason="Travis does not have public key")
def test_public_key_placement(cookies, context):
    context['add_your_pulic_key'] = 'y'
    result = cookies.bake(extra_context=context)

    assert result.exit_code == 0
    # Check if files are not empty
    assert os.path.getsize(str(result.project) + '/ansible_vars/public_keys/app_user_keys') > 0
    assert os.path.getsize(str(result.project) + '/ansible_vars/public_keys/root_user_keys') > 0


@pytest.mark.skipif('TRAVIS' in os.environ,
                    reason="Travis does not have public key")
def test_public_key_placement_disabled(cookies, context):
    context['add_your_pulic_key'] = 'n'
    result = cookies.bake(extra_context=context)

    assert result.exit_code == 0
    # Check if files are empty
    assert os.path.getsize(str(result.project) + '/ansible_vars/public_keys/app_user_keys') == 0
    assert os.path.getsize(str(result.project) + '/ansible_vars/public_keys/root_user_keys') == 0


def test_added_celery_role(cookies, context):
    context['add_celery_support'] = 'y'
    result = cookies.bake(extra_context=context)

    assert result.exit_code == 0
    assert os.path.isdir(str(result.project) + '/roles/celery')


def test_removed_celery_role(cookies, context):
    context['add_celery_support'] = 'n'
    result = cookies.bake(extra_context=context)

    assert result.exit_code == 0
    assert not os.path.isdir(str(result.project) + '/roles/celery')


def test_remove_http_config(cookies, context):
    context['add_letsencrypt_certificate'] = 'y'
    result = cookies.bake(extra_context=context)

    assert result.exit_code == 0
    assert not os.path.isfile(str(result.project) + '/roles/application/templates/nginx_http_config.j2')


def test_remove_https_config(cookies, context):
    context['add_letsencrypt_certificate'] = 'n'
    result = cookies.bake(extra_context=context)

    assert result.exit_code == 0
    assert not os.path.isfile(str(result.project) + '/roles/application/templates/nginx_https_config.j2')
