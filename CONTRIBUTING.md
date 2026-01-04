# Contributing to Campaign Reference

Thank you for your interest in contributing to Campaign Reference! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Node.js 20.x or higher
- npm 9.x or higher
- Python 3.9+ (for data collection scripts)
- Access to Supabase and FEC API keys (for full functionality)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/campaign-reference.git
   cd campaign-reference
   ```

2. Install frontend dependencies:
   ```bash
   cd apps/labs
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env.local
   ```

   Add your Supabase credentials:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Code Style

- We use ESLint and Prettier for code formatting
- Run `npm run lint` before committing
- Follow existing patterns in the codebase
- Use TypeScript for all new code

### Commit Messages

Write clear, concise commit messages:
- Use present tense ("Add feature" not "Added feature")
- Start with a verb (Add, Fix, Update, Remove, Refactor)
- Keep the first line under 72 characters

Examples:
```
Add candidate search by name
Fix notification toggle not persisting
Update README with deployment instructions
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commits
3. Ensure all tests pass and the build succeeds
4. Update documentation if needed
5. Submit a pull request with a clear description

### PR Requirements

- [ ] Code builds without errors (`npm run build`)
- [ ] Lint passes (`npm run lint`)
- [ ] Changes are documented if applicable
- [ ] No sensitive data (API keys, credentials) included

## Project Structure

```
campaign-reference/
├── apps/labs/           # Next.js frontend application
│   ├── src/app/         # App Router pages
│   ├── src/components/  # React components
│   ├── src/contexts/    # React contexts
│   ├── src/hooks/       # Custom hooks
│   └── src/lib/         # Utility libraries
├── database/            # Database migrations
├── scripts/             # Data collection and maintenance scripts
└── .github/             # GitHub Actions workflows
```

## Reporting Issues

When reporting bugs, please include:
- A clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Browser/OS information if relevant
- Screenshots if applicable

## Questions?

Feel free to open an issue for any questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
