# Agent Development Rules

## Basic Principles

### Code Organization
- Follow **Domain-Driven Design (DDD)** principles
- Maintain **Separation of Concerns (SOC)**
- Keep business logic separate from infrastructure code
- Use clear, descriptive names for all entities

### Domain-Driven Design (DDD)
1. **Domain Layer**: Core business logic and entities
   - Keep domain models independent of frameworks
   - Focus on the problem domain, not technical implementation
   - Use ubiquitous language throughout the codebase

2. **Application Layer**: Application-specific business rules
   - Orchestrate domain objects
   - Keep thin - delegate to domain layer

3. **Infrastructure Layer**: Technical implementations
   - Database access, file I/O, external APIs
   - Framework-specific code
   - Separate from business logic

### Separation of Concerns (SOC)
1. **Single Responsibility**: Each module should have one reason to change
2. **Clear Boundaries**: Well-defined interfaces between components
3. **Minimal Coupling**: Reduce dependencies between modules
4. **High Cohesion**: Related functionality should be grouped together

## Project Structure Guidelines

```
src/
├── domain/          # Core business logic and entities
├── application/     # Use cases and application services
├── infrastructure/  # Technical implementations (CV, I/O)
└── presentation/    # UI and user interaction
```

## Code Quality Standards

### Python Specific
- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Write docstrings for all public functions and classes
- Keep functions small and focused (< 20 lines when possible)

### Testing
- Write unit tests for domain logic
- Use integration tests for infrastructure code
- Maintain test coverage above 80%

### Version Control
- Make atomic commits with clear messages
- Keep commits focused on a single concern
- Use meaningful branch names

## Design Patterns
- **Repository Pattern**: For data access abstraction
- **Factory Pattern**: For object creation
- **Strategy Pattern**: For interchangeable algorithms
- **Observer Pattern**: For event-driven updates

## License
This project is licensed under the MIT License - see LICENSE file for details.
