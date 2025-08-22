import pytest
from app import app  # importa o app Flask

# Good: test_example.py
def test_addition():
    assert 1 + 1 == 2