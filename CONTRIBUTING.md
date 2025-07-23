# Contributing to Kale Email API

We love your input! We want to make contributing to Kale as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with GitHub

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [GitHub Flow](https://guides.github.com/introduction/flow/index.html)

Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issue tracker](https://github.com/Kanopusdev/Kale/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/Kanopusdev/Kale/issues/new).

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Development Process

### Setting up your development environment

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/Kale.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Copy environment file: `cp .env.example .env`
7. Edit `.env` with your local configuration
8. Run the application: `uvicorn main:app --reload`

### Code Style

We use [Black](https://black.readthedocs.io/) for code formatting and [flake8](https://flake8.pycqa.org/) for linting.

- Run `black .` to format your code
- Run `flake8 .` to check for linting issues
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes

### Testing

- Write tests for new features and bug fixes
- Run tests with `pytest`
- Ensure all tests pass before submitting a PR
- Aim for good test coverage

### Commit Messages

- Use clear and meaningful commit messages
- Follow the conventional commits format when possible
- Examples:
  - `feat: add email template validation`
  - `fix: resolve JWT token expiration issue`
  - `docs: update API documentation`
  - `test: add unit tests for user authentication`

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature has already been requested
2. Open a new issue with the "enhancement" label
3. Provide a clear description of the feature
4. Explain why this feature would be useful
5. Include any relevant examples or mockups

## Security Issues

If you discover a security vulnerability, please DO NOT open a public issue. Instead, send an email to security@kanopus.org with:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested fixes

We will respond as soon as possible and work with you to resolve the issue.

## Code of Conduct

### Our Pledge

We pledge to make participation in our project and our community a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at conduct@kanopus.org. All complaints will be reviewed and investigated promptly and fairly.

## Recognition

Contributors will be recognized in our README.md file and releases. We appreciate all contributions, no matter how small!

## Questions?

Feel free to contact us:

- **Email**: support@kanopus.org
- **GitHub Issues**: [Create an issue](https://github.com/Kanopusdev/Kale/issues/new)
- **Discussions**: [GitHub Discussions](https://github.com/Kanopusdev/Kale/discussions)

Thank you for contributing to Kale Email API! 🚀
