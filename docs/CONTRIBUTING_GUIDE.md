# FoodSave AI - Contributing Guide

## Overview

Thank you for your interest in contributing to FoodSave AI! This guide will help you understand how to contribute effectively to our project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Standards](#code-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Pull Request Process](#pull-request-process)
6. [Issue Reporting](#issue-reporting)
7. [Documentation](#documentation)
8. [Community Guidelines](#community-guidelines)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Docker (optional but recommended)
- Basic understanding of AI/ML concepts

### First Steps

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/your-username/my_ai_assistant.git
   cd my_ai_assistant
   ```

2. **Set Up Development Environment**
   ```bash
   # Backend setup
   cd src/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Frontend setup
   cd ../../foodsave-frontend
   npm install
   ```

3. **Run the Application**
   ```bash
   # Start backend
   cd src/backend
   uvicorn main:app --reload --port 8000

   # Start frontend (in another terminal)
   cd foodsave-frontend
   npm run dev
   ```

## Development Setup

### Environment Configuration

1. **Copy Environment File**
   ```bash
   cp env.dev.example .env
   ```

2. **Configure Required Variables**
   ```bash
   # Edit .env file with your settings
   DATABASE_URL=postgresql://user:password@localhost:5432/foodsave
   OLLAMA_BASE_URL=http://localhost:11434
   SECRET_KEY=your_development_secret_key
   ```

### Database Setup

```bash
# Create database
createdb foodsave

# Run migrations
cd src/backend
alembic upgrade head

# Seed with test data
python scripts/seed_db.py
```

### AI Model Setup

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama2:7b
ollama pull llama2:13b
```

## Code Standards

### Python Backend

#### Code Style

- Follow PEP 8 style guide
- Use Black for code formatting
- Maximum line length: 88 characters
- Use type hints for all functions

```python
# ✅ Good example
from typing import Dict, List, Optional
from pydantic import BaseModel

class UserPreferences(BaseModel):
    """User preferences for AI recommendations."""

    dietary_restrictions: List[str]
    cooking_skill_level: str
    preferred_cuisines: Optional[List[str]] = None

def process_user_query(
    query: str,
    user_prefs: UserPreferences
) -> Dict[str, any]:
    """
    Process user query with AI assistance.

    Args:
        query: User's natural language query
        user_prefs: User's dietary preferences

    Returns:
        Processed response with recommendations
    """
    # Implementation here
    pass
```

#### Project Structure

```
src/backend/
├── agents/           # AI agents and orchestration
├── api/             # FastAPI endpoints
├── core/            # Core business logic
├── domain/          # Domain models and interfaces
├── infrastructure/  # External service implementations
├── models/          # Database models
├── services/        # Business services
└── tests/           # Test files
```

#### Naming Conventions

- **Files**: snake_case (e.g., `user_service.py`)
- **Classes**: PascalCase (e.g., `UserService`)
- **Functions**: snake_case (e.g., `get_user_preferences`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRY_ATTEMPTS`)
- **Variables**: snake_case (e.g., `user_preferences`)

### Frontend (Next.js)

#### Code Style

- Use TypeScript for all components
- Follow ESLint and Prettier configurations
- Use functional components with hooks
- Implement proper error boundaries

```typescript
// ✅ Good example
import React, { useState, useEffect } from 'react';
import { UserPreferences } from '@/types/user';

interface ChatInterfaceProps {
  userId: string;
  onMessageSend: (message: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  userId,
  onMessageSend,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (content: string) => {
    setIsLoading(true);
    try {
      await onMessageSend(content);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      {/* Component implementation */}
    </div>
  );
};
```

#### Project Structure

```
foodsave-frontend/
├── src/
│   ├── app/          # Next.js app directory
│   ├── components/   # Reusable components
│   ├── hooks/        # Custom React hooks
│   ├── services/     # API services
│   ├── types/        # TypeScript type definitions
│   └── utils/        # Utility functions
├── public/           # Static assets
└── tests/            # Test files
```

## Testing Guidelines

### Backend Testing

#### Unit Tests

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from src.backend.services.user_service import UserService

class TestUserService:
    @pytest.fixture
    def user_service(self):
        return UserService()

    @pytest.fixture
    def mock_user_repo(self):
        return Mock()

    def test_get_user_preferences_success(self, user_service, mock_user_repo):
        # Arrange
        user_id = "test_user_123"
        expected_prefs = {"dietary_restrictions": ["vegetarian"]}
        mock_user_repo.get_preferences.return_value = expected_prefs

        # Act
        result = user_service.get_user_preferences(user_id)

        # Assert
        assert result == expected_prefs
        mock_user_repo.get_preferences.assert_called_once_with(user_id)
```

#### Integration Tests

```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)

def test_chat_endpoint():
    response = client.post(
        "/api/v1/chat",
        json={"message": "What can I cook with tomatoes?"}
    )
    assert response.status_code == 200
    assert "response" in response.json()
```

#### Performance Tests

```python
# tests/performance/test_ai_response_time.py
import time
import pytest
from src.backend.agents.chef_agent import ChefAgent

def test_ai_response_time():
    agent = ChefAgent()
    start_time = time.time()

    response = agent.process_query("Suggest a quick dinner recipe")

    end_time = time.time()
    response_time = end_time - start_time

    assert response_time < 5.0  # Should respond within 5 seconds
    assert response is not None
```

### Frontend Testing

#### Component Tests

```typescript
// tests/components/ChatInterface.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInterface } from '@/components/chat/ChatInterface';

describe('ChatInterface', () => {
  const mockOnMessageSend = jest.fn();

  beforeEach(() => {
    mockOnMessageSend.mockClear();
  });

  it('should send message when form is submitted', () => {
    render(
      <ChatInterface
        userId="test-user"
        onMessageSend={mockOnMessageSend}
      />
    );

    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'Hello AI!' } });
    fireEvent.click(sendButton);

    expect(mockOnMessageSend).toHaveBeenCalledWith('Hello AI!');
  });
});
```

#### E2E Tests

```typescript
// tests/e2e/chat-flow.spec.ts
import { test, expect } from '@playwright/test';

test('complete chat flow', async ({ page }) => {
  await page.goto('/chat');

  // Type a message
  await page.fill('[data-testid="message-input"]', 'What can I cook?');
  await page.click('[data-testid="send-button"]');

  // Wait for AI response
  await expect(page.locator('[data-testid="ai-response"]')).toBeVisible();

  // Verify response contains cooking suggestions
  const response = await page.textContent('[data-testid="ai-response"]');
  expect(response).toContain('recipe');
});
```

### Test Coverage Requirements

- **Backend**: Minimum 80% code coverage
- **Frontend**: Minimum 70% code coverage
- **Critical paths**: 100% coverage required

## Pull Request Process

### Before Submitting

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clear, documented code
   - Add appropriate tests
   - Update documentation if needed

3. **Run Tests**
   ```bash
   # Backend tests
   cd src/backend
   pytest --cov=src --cov-report=html

   # Frontend tests
   cd foodsave-frontend
   npm test
   npm run test:e2e
   ```

4. **Code Quality Checks**
   ```bash
   # Backend
   black src/
   flake8 src/
   mypy src/

   # Frontend
   npm run lint
   npm run type-check
   ```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes introduced

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks**
   - CI/CD pipeline runs tests
   - Code coverage is checked
   - Linting and formatting verified

2. **Code Review**
   - At least one maintainer must approve
   - Address all review comments
   - Update PR if requested

3. **Merge**
   - Squash commits if needed
   - Use conventional commit messages
   - Delete feature branch after merge

## Issue Reporting

### Bug Reports

```markdown
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Browser: [e.g., Chrome 120]
- Python: [e.g., 3.11.0]
- Node.js: [e.g., 18.17.0]

**Additional Context**
Screenshots, logs, etc.
```

### Feature Requests

```markdown
**Feature Description**
Clear description of the feature

**Use Case**
Why this feature is needed

**Proposed Solution**
How you think it should work

**Alternative Solutions**
Other approaches considered

**Additional Context**
Any relevant information
```

## Documentation

### Code Documentation

- Use docstrings for all public functions and classes
- Include type hints
- Provide usage examples

```python
def analyze_food_waste(user_id: str, time_period: str) -> Dict[str, any]:
    """
    Analyze user's food waste patterns.

    This function processes user's shopping and consumption data
    to identify waste patterns and provide recommendations.

    Args:
        user_id: Unique identifier for the user
        time_period: Analysis period ('week', 'month', 'year')

    Returns:
        Dictionary containing:
        - waste_score: Float between 0-10
        - recommendations: List of improvement suggestions
        - patterns: Identified waste patterns

    Raises:
        UserNotFoundError: If user_id doesn't exist
        InvalidTimePeriodError: If time_period is invalid

    Example:
        >>> result = analyze_food_waste("user123", "month")
        >>> print(result['waste_score'])
        3.5
    """
    pass
```

### API Documentation

- Use OpenAPI/Swagger for API documentation
- Include request/response examples
- Document error codes and messages

### User Documentation

- Write clear, step-by-step guides
- Include screenshots and videos
- Provide troubleshooting sections

## Community Guidelines

### Code of Conduct

1. **Be Respectful**
   - Treat all contributors with respect
   - Use inclusive language
   - Be patient with newcomers

2. **Be Helpful**
   - Answer questions constructively
   - Provide detailed feedback
   - Share knowledge and resources

3. **Be Professional**
   - Keep discussions on-topic
   - Follow project guidelines
   - Maintain confidentiality when needed

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions and reviews
- **Documentation**: User guides and technical docs

### Recognition

- Contributors are recognized in the project README
- Significant contributions are highlighted in release notes
- Regular contributors may be invited to join the maintainer team

## Getting Help

### Resources

- [Project Documentation](docs/)
- [API Reference](docs/API_REFERENCE.md)
- [Architecture Guide](docs/ARCHITECTURE_DOCUMENTATION.md)
- [Testing Guide](docs/TESTING_GUIDE.md)

### Support

- Create an issue for bugs or feature requests
- Use GitHub Discussions for questions
- Join our community chat (if available)

---

**Thank you for contributing to FoodSave AI!**

**Last Updated**: December 22, 2024
**Version**: 1.0
**Maintainer**: FoodSave AI Team
