import pytest
from matrixcurator_benchmark.core.execution import expand_permutations, execute_single_run
from matrixcurator_benchmark.core.decorators import parametrize
from matrixcurator_benchmark.core.exceptions import SkipBenchmark, FailBenchmark

def test_expand_permutations_no_metadata():
    def func():
        pass
    
    permutations = list(expand_permutations(func))
    assert permutations == [{}]

def test_expand_permutations_multiple():
    @parametrize("b", [3, 4])
    @parametrize("a", [1, 2])
    def func():
        pass
        
    permutations = list(expand_permutations(func))
    assert len(permutations) == 4
    assert {"a": 1, "b": 3} in permutations

@pytest.mark.asyncio
async def test_execute_single_run_sync():
    def sync_func(x):
        return x * 2
        
    result = await execute_single_run(sync_func, {"x": 5})
    assert result == 10

@pytest.mark.asyncio
async def test_execute_single_run_async():
    async def async_func(x):
        return x * 2
        
    result = await execute_single_run(async_func, {"x": 5})
    assert result == 10

@pytest.mark.asyncio
async def test_execute_single_run_skip_fail(caplog):
    caplog.set_level("DEBUG")
    def skip_func():
        raise SkipBenchmark("Skip")
        
    with pytest.raises(SkipBenchmark):
        await execute_single_run(skip_func, {})
    assert "Skipped benchmark: skip_func - Skip" in caplog.text
    # We could also test the level, caplog.records has it
    assert any(record.levelname == "DEBUG" and "Skipped benchmark" in record.message for record in caplog.records)
        
    def fail_func():
        raise FailBenchmark("Fail")
        
    with pytest.raises(FailBenchmark):
        await execute_single_run(fail_func, {})
