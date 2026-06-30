# Move

Move is a *self hosted* application to visualize your movements 

## Getting Started

1. Create a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Run the application:
   ```bash
   PYTHONPATH=src python3 -m move.main
   ```

## Running Tests

Execute the unit tests using `pytest`:
```bash
PYTHONPATH=src pytest
```
