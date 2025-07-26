# Minty Test Suite

This directory contains comprehensive tests for the Minty stock analysis dashboard project.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_api.py              # Backend API endpoint tests
├── test_model.py            # Machine learning model tests
├── test_frontend.js         # Frontend JavaScript tests
├── test_integration.py      # Integration tests
├── requirements-test.txt    # Testing dependencies
└── README.md               # This file
```

## Test Categories

### 1. **Backend API Tests** (`test_api.py`)
- **Authentication endpoints**: Register, login, logout
- **Stock data endpoints**: Live data, historical data, predictions, recommendations
- **User management**: Profile, orders, user info
- **Error handling**: Invalid requests, missing data, authentication failures

### 2. **ML Model Tests** (`test_model.py`)
- **Feature creation**: Technical indicators, data preprocessing
- **Model training**: Data loading, model fitting, validation
- **Predictions**: Price predictions, recommendation generation
- **Data validation**: Edge cases, missing data, invalid inputs

### 3. **Frontend Tests** (`test_frontend.js`)
- **Authentication**: Login/logout flow, token management
- **API calls**: Data fetching, error handling
- **Chart functionality**: Chart creation, data visualization
- **UI updates**: DOM manipulation, user interactions
- **Performance**: Response times, memory usage

### 4. **Integration Tests** (`test_integration.py`)
- **Full user journey**: Registration to logout
- **Data consistency**: Cross-endpoint data validation
- **Performance**: Response times, concurrent requests
- **Security**: Authentication, CORS, injection protection
- **Database**: Relationships, transactions, data integrity

## Running Tests

### Backend Tests (Python)

```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Run all tests
pytest

# Run specific test categories
pytest tests/test_api.py          # API tests only
pytest tests/test_model.py        # Model tests only
pytest tests/test_integration.py  # Integration tests only

# Run with coverage
pytest --cov=backend --cov-report=html

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_api.py::TestAuthEndpoints::test_login_success

# Run tests in parallel
pytest -n auto

# Run only fast tests (exclude slow ones)
pytest -m "not slow"
```

### Frontend Tests (JavaScript)

```bash
# Install dependencies
npm install

# Run all frontend tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test categories
npm run test:unit
npm run test:integration

# Lint code
npm run lint
npm run lint:fix

# Format code
npm run format
```

### Test Markers

Use pytest markers to run specific test categories:

```bash
# Unit tests
pytest -m unit

# Integration tests
pytest -m integration

# Performance tests
pytest -m performance

# Security tests
pytest -m security

# Slow tests (exclude for quick runs)
pytest -m "not slow"
```

## Test Configuration

### Pytest Configuration (`conftest.py`)

- **Fixtures**: Reusable test data and mocks
- **Mocking**: External APIs, database, file system
- **Test data**: Sample stock data, user data, order data
- **Performance tools**: Timers, memory monitors
- **Markers**: Custom test categorization

### Jest Configuration (`package.json`)

- **Environment**: jsdom for DOM testing
- **Coverage**: 70% threshold for all metrics
- **Transformers**: Babel for modern JavaScript
- **Mocking**: Chart.js, fetch API, localStorage

## Test Data

### Sample Data Fixtures

- **Stock Data**: Realistic price movements, volumes, dates
- **User Data**: Usernames, emails, passwords
- **Order Data**: Buy/sell orders with quantities and prices
- **Profile Data**: User preferences and settings

### Mock External Services

- **yfinance**: Stock data API
- **Finnhub**: News API
- **Database**: PostgreSQL with test data
- **JWT**: Authentication tokens

## Coverage Requirements

### Backend Coverage
- **Lines**: 80% minimum
- **Functions**: 80% minimum
- **Branches**: 70% minimum
- **Statements**: 80% minimum

### Frontend Coverage
- **Lines**: 70% minimum
- **Functions**: 70% minimum
- **Branches**: 70% minimum
- **Statements**: 70% minimum

## Performance Benchmarks

### API Response Times
- **Live data**: < 500ms
- **Historical data**: < 1s
- **Predictions**: < 2s
- **Recommendations**: < 1s

### Memory Usage
- **Per request**: < 10MB increase
- **Total application**: < 100MB baseline

### Concurrent Requests
- **5 simultaneous requests**: All successful
- **Error handling**: Graceful degradation

## Security Testing

### Authentication
- **Valid tokens**: Accepted
- **Invalid tokens**: Rejected (401/422)
- **Expired tokens**: Handled gracefully
- **Missing tokens**: Redirected to login

### Input Validation
- **SQL injection**: Protected against
- **XSS attacks**: Sanitized inputs
- **Malformed JSON**: Error responses
- **Missing fields**: Validation errors

### CORS
- **Cross-origin requests**: Properly handled
- **Headers**: Correctly set
- **Methods**: Allowed methods enforced

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      - name: Run backend tests
        run: pytest --cov=backend --cov-report=xml
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install frontend dependencies
        run: npm install
      - name: Run frontend tests
        run: npm test
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Best Practices

### Writing Tests

1. **Arrange-Act-Assert**: Clear test structure
2. **Descriptive names**: Test names explain what they test
3. **Single responsibility**: Each test focuses on one thing
4. **Independent**: Tests don't depend on each other
5. **Fast**: Tests run quickly (< 1s each)
6. **Deterministic**: Same result every time

### Test Data

1. **Realistic**: Use realistic but fake data
2. **Minimal**: Only include necessary data
3. **Consistent**: Use fixtures for repeated data
4. **Clean**: Reset state between tests

### Mocking

1. **External dependencies**: Mock APIs, databases, file system
2. **Time**: Mock time for consistent results
3. **Randomness**: Seed random generators
4. **Network**: Mock HTTP requests

### Error Testing

1. **Happy path**: Test successful scenarios
2. **Error paths**: Test failure scenarios
3. **Edge cases**: Test boundary conditions
4. **Invalid inputs**: Test malformed data

## Troubleshooting

### Common Issues

1. **Import errors**: Check Python path and virtual environment
2. **Database errors**: Ensure test database is configured
3. **Mock failures**: Verify mock setup and teardown
4. **Timeout errors**: Increase timeout for slow tests
5. **Coverage gaps**: Add tests for uncovered code

### Debugging Tests

```bash
# Run with debug output
pytest -s -v

# Run single test with debugger
pytest --pdb tests/test_api.py::test_specific_function

# Run with print statements
pytest -s

# Generate coverage report
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

## Contributing

### Adding New Tests

1. **Follow naming convention**: `test_*.py` for Python, `*.test.js` for JavaScript
2. **Use appropriate fixtures**: Leverage existing fixtures in `conftest.py`
3. **Add to correct category**: Unit, integration, or performance tests
4. **Update documentation**: Document new test functionality
5. **Maintain coverage**: Ensure new code is tested

### Test Review Checklist

- [ ] Tests are descriptive and well-named
- [ ] Tests cover both success and failure cases
- [ ] Tests are independent and don't affect each other
- [ ] Tests use appropriate mocks and fixtures
- [ ] Tests maintain or improve coverage
- [ ] Tests follow project coding standards
- [ ] Tests are fast and reliable

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing Best Practices](https://martinfowler.com/articles/microservice-testing/)
- [Python Testing with pytest](https://pytest.org/en/stable/)
- [JavaScript Testing with Jest](https://jestjs.io/docs/getting-started) 