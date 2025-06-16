# Backend Refactoring Plan for foodsave-ai

## 1. API Structure Improvements
- [ ] **Versioning**: Move to `/api/v2` for future changes
- [ ] **Router Organization**: Group related endpoints (e.g., all chat endpoints together)
- [ ] **Response Models**: Standardize response formats across endpoints
- [ ] **Middleware**: Extract middleware to `src/backend/middleware/` directory

## 2. Dependency Management
- [ ] **Group Dependencies**: Create separate groups in pyproject.toml:
  - `ai` (Ollama, PyMuPDF)
  - `db` (SQLAlchemy, aiosqlite)
  - `api` (FastAPI, uvicorn)
- [ ] **Update Dependencies**: Review and update to latest stable versions
- [ ] **Remove Unused**: Audit and remove unused dependencies

## 3. Error Handling
- [ ] **Custom Exceptions**: Create in `src/backend/exceptions.py`
- [ ] **Error Codes**: Standardize error codes/messages
- [ ] **Logging**: Improve error logging with context
- [ ] **Validation**: Enhance Pydantic validation messages

## 4. Configuration
- [ ] **Environment Variables**: Move hardcoded values to .env
- [ ] **Settings Class**: Enhance `config.py` with validation
- [ ] **Secrets Management**: Implement proper secrets handling

## 5. Testing
- [ ] **Test Coverage**: Increase to >90%
- [ ] **Test Organization**:
  - Unit tests: Test individual components
  - Integration tests: Test API endpoints
  - E2E tests: Test full workflows
- [ ] **Test Data**: Create reusable fixtures
- [ ] **Mocking**: Implement proper mocking for external services

## 6. Documentation
- [ ] **API Docs**: Add OpenAPI/Swagger
- [ ] **Code Comments**: Ensure all major components are documented
- [ ] **Developer Guide**: Create CONTRIBUTING.md

## Implementation Roadmap
1. Week 1: API Structure + Dependency Management
2. Week 2: Error Handling + Configuration
3. Week 3: Testing Improvements
4. Week 4: Documentation

Would you like me to:
1. Implement any of these changes
2. Provide more details on specific items
3. Create separate issues/tickets for each task
4. Switch to code mode to begin implementation
