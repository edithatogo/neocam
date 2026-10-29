"""Report benchmark measurements without passing missing or failing runs."""
import importlib
import pytest


def api():
    try:return importlib.import_module('quality.benchmark')
    except ModuleNotFoundError:pytest.fail('Benchmark implementation missing')


def test_only_successful_equivalent_samples_can_be_compared():
    m=api()
    rows=[{'variant':'old','duration_seconds':4,'returncode':0,'passed':10},
          {'variant':'old','duration_seconds':6,'returncode':0,'passed':10},
          {'variant':'new','duration_seconds':2,'returncode':0,'passed':10},
          {'variant':'new','duration_seconds':3,'returncode':0,'passed':10}]
    out=m.summarise(rows)
    assert out['median_seconds']['old'] == 5
    assert out['median_seconds']['new'] == 2.5
    assert out['speedup'] == 2


def test_failing_samples_are_not_silently_dropped():
    with pytest.raises(ValueError):api().summarise([{'variant':'old','duration_seconds':4,'returncode':1,'passed':10}])


def test_different_test_counts_rejected():
    rows=[{'variant':'old','duration_seconds':4,'returncode':0,'passed':10},
          {'variant':'new','duration_seconds':2,'returncode':0,'passed':9}]
    with pytest.raises(ValueError):api().summarise(rows)


def test_benchmark_streams_logs_and_accepts_relative_path(tmp_path,monkeypatch):
    m=api();monkeypatch.setattr(m,'ROOT',tmp_path)
    class Completed:
        returncode=0
    def run(command,**kwargs):
        assert not kwargs.get('capture_output',False)
        kwargs['stdout'].write('10 passed in 0.1s\n')
        kwargs['stdout'].flush()
        return Completed()
    monkeypatch.setattr(m.subprocess,'run',run)
    row=m.timed([('pytest',)],__import__('pathlib').Path('result.txt'))
    assert row['returncode']==0 and row['passed']==10
    assert (tmp_path/'result.txt').exists()


def test_benchmark_empty_command_list_is_invalid(tmp_path):
    with pytest.raises(ValueError):api().timed([],tmp_path/'result.txt')
