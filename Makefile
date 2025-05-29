.PHONY: lint format check clean test test-mock-server setup-venv

# Python files
PYTHON_FILES := $(shell find custom_components -name "*.py")

# Default target
all: lint

# Note: If you're using a virtual environment, activate it before running these commands
# Example: source venv/bin/activate

# Setup virtual environment
setup-venv:
	python -m venv .venv
	pip install -r requirements.txt
	@echo "Virtual environment created at .venv/"
	@echo "To activate, run: source .venv/bin/activate"

# Run all linters
lint: ruff

# Run ruff linter
ruff:
	python -m ruff check custom_components

# Format code with black and isort
format:
	python -m isort custom_components
	python -m black custom_components

# Check formatting without making changes
check:
	python -m isort --check-only custom_components
	python -m black --check custom_components

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete

test: test-mock-server

# Run mock server tests (for CI)
test-mock-server:
	@echo "Starting mock Modbus server..."
	python mock-server/mock_modbus_server.py & echo $$! > .mock_server.pid
	@echo "Waiting for server to initialize..."
	sleep 2
	@echo "Running test script..."
	python mock-server/test_mock_server.py || (kill `cat .mock_server.pid` 2>/dev/null; rm -f .mock_server.pid; exit 1)
	@echo "Stopping mock server..."
	kill `cat .mock_server.pid` 2>/dev/null || true
	rm -f .mock_server.pid
	@echo "Mock server test completed"

# Help target
help:
	@echo "Available targets:"
	@echo "  all        : Run all linters (default)"
	@echo "  setup-venv : Create a virtual environment at .venv/"
	@echo "  lint       : Run all linters"
	@echo "  ruff       : Run ruff linter"
	@echo "  format     : Format code with black and isort"
	@echo "  check      : Check formatting without making changes"
	@echo "  clean      : Clean up cache files"
	@echo "  test-mock-server : Run the mock Modbus server tests"
	@echo "  help       : Show this help message"
