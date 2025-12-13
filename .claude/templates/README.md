# Code Templates

This directory contains templates for common code patterns used in the Subscription Tracker project.

## Available Templates

### Backend (Python)

#### `python_service.py`
Template for creating a new service class following the repository pattern.

**Usage:**
1. Copy the template to `src/services/your_service.py`
2. Replace `[ServiceName]` with your service name (e.g., `Notification`)
3. Replace `[entity]` with your entity name (e.g., `notification`)
4. Implement the business logic in each method

**Key features:**
- Async database operations
- Type hints throughout
- Google-style docstrings
- Standard CRUD methods
- Error handling patterns

#### `fastapi_router.py`
Template for creating REST API endpoints with FastAPI.

**Usage:**
1. Copy to `src/api/your_resource.py`
2. Replace `[resource]` and `[resources]` with singular/plural names
3. Update import statements for your schemas
4. Customize endpoint logic as needed

**Key features:**
- RESTful endpoint structure
- Proper HTTP status codes
- Dependency injection pattern
- Error handling with HTTPException
- OpenAPI documentation

### Frontend (TypeScript/React)

#### `react_component.tsx`
Template for creating React components with TypeScript.

**Usage:**
1. Copy to `frontend/src/components/YourComponent.tsx`
2. Replace `[ComponentName]` with your component name (PascalCase)
3. Update props interface
4. Implement component logic

**Key features:**
- TypeScript interface for props
- JSDoc comments for documentation
- useState example
- Tailwind CSS classes
- Proper prop typing

#### `react_hook.ts`
Template for creating custom React hooks.

**Usage:**
1. Copy to `frontend/src/hooks/useYourHook.ts`
2. Replace `[HookName]` with your hook name (PascalCase without "use")
3. Replace `[DataType]` with your data type
4. Implement hook logic

**Key features:**
- TypeScript interfaces for options and return type
- Async operation pattern
- Loading and error states
- Success/error callbacks
- useEffect integration

## Template Conventions

### Naming Placeholders

- `[ComponentName]` - Replace with PascalCase name (e.g., `SubscriptionList`)
- `[ServiceName]` - Replace with PascalCase name (e.g., `Subscription`)
- `[resource]` - Replace with lowercase singular (e.g., `subscription`)
- `[resources]` - Replace with lowercase plural (e.g., `subscriptions`)
- `[entity]` - Replace with lowercase singular (e.g., `user`)
- `[DataType]` - Replace with TypeScript type (e.g., `Subscription[]`)
- `[HookName]` - Replace with hook name without "use" prefix (e.g., `Subscriptions`)

### Import Statements

Remember to update import paths when using templates:
- Adjust relative imports based on file location
- Import correct schemas/models for your feature
- Add any additional dependencies needed

### Documentation

All templates include:
- Comprehensive JSDoc/docstring comments
- Type annotations
- Usage examples
- Clear parameter descriptions

## Best Practices

1. **Always customize the template** - Don't leave placeholder text
2. **Update documentation** - Modify docstrings to match your implementation
3. **Follow project standards** - Refer to coding standards in `.claude/docs/`
4. **Add tests** - Create corresponding test files for new code
5. **Run linters** - Ensure code passes Ruff/ESLint checks before committing

## Related Documentation

- [Python Coding Standards](../docs/PYTHON_STANDARDS.md)
- [TypeScript Coding Standards](../docs/TYPESCRIPT_STANDARDS.md)
- [System Architecture](../docs/ARCHITECTURE.md)
