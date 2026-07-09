# Python code review guidelines

## General guidelines

### Correctness

- Is the logic correct? Are there missing boundary conditions?
- Are exceptions handled properly?
- Is it thread-safe in concurrent scenarios?

### Security

- Are there security vulnerabilities such as SQL injection or XSS?
- Is sensitive information handled correctly?
- Is permission validation complete?

### Performance

- Are there obvious performance issues (e.g., N+1 queries, unnecessary loops)?
- Are resources properly released?

### Maintainability

- Is the code clear and easy to understand?
- Do names accurately express intent?
- Does it follow the project’s existing code style and architecture patterns?

### Test Coverage

- Do critical logic paths have corresponding test cases?
- Do test cases cover boundary conditions?

## Python guidelines

Combine with general guidelines.

### Styleguide

- All code should follow PEP 8.
- Wherever possible, code should be idiomatic per the library/module it reuses.

### Type Annotations

- All production code must have complete type annotations; do not use `Any` when a more specific type is available
- Use `type: ignore` only with a comment explaining why the suppression is necessary
- Use `TypeAlias` for complex type aliases and document them with a docstring directly below the assignment
- Prefer modern type syntax, like `|` union syntax over `Optional[T]` or `Union[T, U]`

### Docstrings and Documentation

- Docstrings describe semantics, not types
- Module docstrings briefly describe what the module contains and when to use it
- Class docstrings explain the class's purpose; list public attributes only when not obvious from annotations
- Method and function docstrings use Google-style sections: `Parameters:`, `Returns:`, `Yields:`, `Receives:`, `Raises:`, `Warns:`, `Examples:`
- Exception classes must document when they are raised
- Magic methods (`__init__`, `__repr__`, etc.) should be documented when they are part of the public API

### Naming Conventions

- Use `snake_case` for functions, methods, and variables
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants
- Test modules follow `test_*.py`, test functions `test_*`, test classes `Test*`

### Performance and Memory

- Core classes must use `__slots__` to reduce memory overhead
- Avoid unnecessary allocations in hot paths
- Prefer iterator adapters and standard library collection APIs

### Error Handling

- Errors should not be converted to strings too early or discarded without context
- Public APIs should not panic on ordinary invalid input; return typed errors instead

### Testing

- Aim for 100% test coverage on all changes
- Add unit tests alongside the module being changed, following existing patterns
- Add cross-engine test cases to `test_exports.json` when modifying output behavior
- All output changes should be covered with unit tests, integration tests, and snapshot tests
- When property-based tests find a failing example on realistic input, fix the bug and pin it with `@example(...)`

### Commits

- Commit messages should be concise, in imperative mood, and use Sentence case (no Title Case)

### Security

- Do not log secrets, tokens, credentials, private keys, or personally identifiable information
- Validate path, URL, command, and serialized input before use
- Check integer conversions and length arithmetic for overflow and boundary errors

## Project-specific guidelines

Combine with general and Python guidelines.

### Engines

- Engines share the same interface but are not guaranteed to produce byte-identical output for the same input — accepted differences exist
- Review engine changes with the understanding that each engine delegates serialization to a different underlying library
