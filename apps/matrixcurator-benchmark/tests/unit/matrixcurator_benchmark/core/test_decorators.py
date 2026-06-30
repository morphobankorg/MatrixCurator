import pytest
from unittest.mock import patch, ANY

from matrixcurator_benchmark.core.decorators import benchmark, parametrize, fixture

@patch("matrixcurator_benchmark.core.decorators.add_benchmark")
def test_benchmark_decorator(mock_add_benchmark):
    @benchmark(dataset_name="test_dataset")
    def sample_func():
        pass
    
    assert hasattr(sample_func, "__benchmark_metadata__")
    assert sample_func.__benchmark_metadata__["dataset_name"] == "test_dataset"
    mock_add_benchmark.assert_called_once_with(
        ANY, sample_func.__benchmark_metadata__
    )

def test_parametrize_decorator():
    @parametrize("arg1", [1, 2])
    @parametrize("arg2,arg3", [(3, 4)])
    def sample_func():
        pass
        
    assert hasattr(sample_func, "__benchmark_metadata__")
    params = sample_func.__benchmark_metadata__["parametrizations"]
    assert len(params) == 2
    
    assert params[0]["argnames"] == "arg2,arg3"
    assert params[0]["argvalues"] == [(3, 4)]
    assert params[1]["argnames"] == "arg1"
    assert params[1]["argvalues"] == [1, 2]

@patch("matrixcurator_benchmark.core.decorators.add_fixture")
def test_fixture_decorator(mock_add_fixture):
    @fixture(scope="session", name="custom_name")
    def sample_fixture():
        return 1
        
    mock_add_fixture.assert_called_once_with("custom_name", ANY, "session")

@patch("matrixcurator_benchmark.core.decorators.add_fixture")
def test_fixture_decorator_default_name(mock_add_fixture):
    @fixture(scope="function")
    def default_name_fixture():
        return 2
        
    mock_add_fixture.assert_called_once_with("default_name_fixture", ANY, "function")
