# Contributing to Job Market Intelligence

Thank you for considering contributing to this project! Here are some guidelines to help you get started.

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/job-market-intelligence.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
5. Install dependencies: `pip install -r requirements.txt`
6. Install dev dependencies: `pip install pytest pytest-cov black flake8 mypy`

## Code Standards

- **Code Style**: We use [Black](https://github.com/psf/black) for formatting
  ```bash
  black .
  ```

- **Linting**: Run flake8 before committing
  ```bash
  flake8 . --max-line-length=100
  ```

- **Type Hints**: Add type hints to all functions
  ```bash
  mypy . --ignore-missing-imports
  ```

- **Documentation**: Add docstrings to all public functions following Google style

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting PR
  ```bash
  pytest tests/ -v
  pytest tests/ --cov=. --cov-report=html
  ```

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes with appropriate tests
3. Run all quality checks (black, flake8, pytest)
4. Commit with clear messages: `git commit -m "Add: your feature description"`
5. Push to your fork: `git push origin feature/your-feature-name`
6. Open a Pull Request with:
   - Clear description of changes
   - References to related issues
   - Screenshots if applicable

## Reporting Issues

- Use the [issue tracker](https://github.com/your-username/job-market-intelligence/issues)
- Provide clear reproduction steps
- Include error messages and logs
- Specify your environment (OS, Python version)

## Feature Requests

- Open an issue with the "enhancement" label
- Describe the use case and expected behavior
- Discuss before implementing large features

## Questions?

Feel free to open an issue with the "question" label or contact the maintainers.

Thank you for contributing! 🎉
