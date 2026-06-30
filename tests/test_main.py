from move.main import greet


def test_greet() -> None:
    """Test the greet function returns the expected greeting."""
    assert greet() == "Hello, World!"
    assert greet("Developer") == "Hello, Developer!"
