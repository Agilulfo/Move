def greet(name: str = "World") -> str:
    """Returns a greeting message."""
    return f"Hello, {name}!"


def main() -> None:
    """Main execution entry point."""
    print(greet())


if __name__ == "__main__":
    main()
