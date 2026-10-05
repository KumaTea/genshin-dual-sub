"""下载器：默认不下载，同意后才下；URL 拼接正确。"""

import os

import pytest

from cpl import download
from share.config import Settings


@pytest.fixture
def fresh_settings(tmp_path, monkeypatch):
    settings = Settings(str(tmp_path / 'config.ini'))
    monkeypatch.setattr(download, 'settings', settings)
    return settings


def test_default_base_url_points_at_main_branch(fresh_settings):
    """旧代码用的是 master 分支，现在那个地址 404。"""
    url = download.base_url()
    assert '/-/raw/main/' in url
    assert 'master' not in url


def test_file_url(fresh_settings):
    url = download.file_url('TextMapCHS.json')
    assert url.endswith('/TextMap/TextMapCHS.json?inline=false')


def test_no_consent_means_no_download(fresh_settings, tmp_path, monkeypatch):
    """默认配置下不能偷偷下载。"""
    monkeypatch.setattr(download, 'ask_consent', lambda names: False)
    called = []
    monkeypatch.setattr(download, 'download_file', lambda *a: called.append(a) or True)

    missing = download.download_missing(['A.json', 'B.json'], str(tmp_path))
    assert missing == ['A.json', 'B.json']
    assert called == [], '没同意就不该发起下载'


def test_consent_triggers_download(fresh_settings, tmp_path, monkeypatch):
    monkeypatch.setattr(download, 'ask_consent', lambda names: True)
    downloaded = []

    def fake(name, target):
        downloaded.append(name)
        return True

    monkeypatch.setattr(download, 'download_file', fake)
    assert download.download_missing(['A.json'], str(tmp_path)) == []
    assert downloaded == ['A.json']


def test_existing_files_are_skipped(fresh_settings, tmp_path, monkeypatch):
    (tmp_path / 'A.json').write_text('{}', encoding='utf-8')
    monkeypatch.setattr(download, 'ask_consent',
                        lambda names: pytest.fail('文件已存在，不该再问'))
    assert download.download_missing(['A.json'], str(tmp_path)) == []


def test_allow_download_flag_skips_prompt(fresh_settings, monkeypatch):
    fresh_settings.set('download', 'allow_download', 1)
    monkeypatch.setattr(download.sys, 'stdin', None)
    assert download.ask_consent(['A.json']) is True


def test_non_interactive_without_flag_refuses(fresh_settings, monkeypatch):
    monkeypatch.setattr(download.sys, 'stdin', None)
    assert download.ask_consent(['A.json']) is False


def test_failed_download_leaves_no_partial_file(fresh_settings, tmp_path, monkeypatch):
    class Boom:
        def __enter__(self):
            raise OSError('network down')

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(download.urllib.request, 'urlopen', lambda *a, **k: Boom())
    assert download.download_file('A.json', str(tmp_path)) is False
    assert not os.path.exists(tmp_path / 'A.json')
    assert not os.path.exists(tmp_path / 'A.json.part')


@pytest.mark.parametrize('size,expected', [
    (512, '512.0B'), (2048, '2.0KB'), (5 * 1024 ** 2, '5.0MB'),
])
def test_format_size(size, expected):
    assert download._format_size(size) == expected
