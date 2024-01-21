import os
import pytest
from pathlib import Path
from openapi_spec_validator import validate
from atomically import Atomically

atomic_files_dir = os.path.join(os.getcwd(), "tests", "atomic_files")
atomic_files = os.listdir(atomic_files_dir)
generated_files_dir = os.path.join(os.getcwd(), "tests", "generated_files")


@pytest.mark.parametrize("atomic_file", atomic_files)
def test_example_function(snapshot, atomic_file):
    atomic_file_path = os.path.join(atomic_files_dir, atomic_file)
    atomic = Atomically.from_file(atomic_file_path)
    validate(atomic.content)
    openapi = atomic.generate()
    validate(openapi.content)
    snapshot_test_name = Path(atomic_file).stem
    snapshot.assert_match(openapi.content, snapshot_test_name)
    generated_file_path = os.path.join(generated_files_dir, atomic_file)
    with open(generated_file_path, "w") as f:
        f.write(openapi.to_yaml())
