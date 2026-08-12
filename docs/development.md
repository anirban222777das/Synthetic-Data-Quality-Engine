# Development Guide

This guide covers how to set up the development environment, run the test suite, and extend the core mathematical capabilities of the analyzer and generator.

## Local Setup

We recommend using a standard Python virtual environment.

```bash
# Clone the repository
git clone https://github.com/your-org/synthetic-data-quality.git
cd synthetic-data-quality

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running Tests

The project uses `pytest` for all unit testing. The test suite covers deterministic generation, boundary enforcement, and statistical correctness.

```bash
pytest tests/ -v
```

Ensure all tests pass before proposing a pull request. We strictly enforce that generation remains mathematically deterministic when a seed is provided.

## Reproducibility

When developing new generation strategies, you **must** ensure they are deterministic. 

```python
# GOOD: Using a seeded NumPy generator
rng = np.random.default_rng(seed)
samples = rng.uniform(min, max, size)

# BAD: Using global state
import random
samples = [random.uniform(min, max) for _ in range(size)]
```

If an output varies between test runs without changing the underlying seed, the PR will be rejected.

## Adding a New Sampling Strategy

If you wish to add a new distribution strategy (e.g., Log-Normal, Weibull):

1. **Analyze (analyzer.py)**: Add the necessary parameter extraction (e.g., shape/scale parameters) to `DatasetAnalyzer._analyze_numeric_column`.
2. **Schema (schema.py)**: Add the extracted parameters to the `ColumnSchema` dataclass.
3. **Generate (generator.py)**: Add the new branching logic inside `SyntheticGenerator._generate_numeric_column` and call the corresponding SciPy distribution.
4. **Test (test_generator.py)**: Write a unit test ensuring the distribution accurately mirrors a mathematically pure reference distribution, and verify it behaves deterministically.
