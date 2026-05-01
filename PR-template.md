## Summary

<!-- What does this PR do? Why is it needed? Link any related issues. -->

Closes #

---

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor
- [ ] Configuration / DevOps
- [ ] Documentation

---

## Checklist

### Code Quality
- [ ] Linter passes locally (`make lint`)
- [ ] No commented-out or debug code left in
- [ ] New functions/classes have docstrings

### Tests
- [ ] Tests pass locally (`make test`)
- [ ] New code is covered by tests
- [ ] Edge cases are handled

### Security
- [ ] No secrets, API keys, or credentials in the code
- [ ] User input is validated and sanitized
- [ ] Role/permission checks are in place where needed
- [ ] `bandit` and `safety` pass (`make security`)

### Database
- [ ] Migration included if schema changed (`make migrate`)
- [ ] Migration is reversible (downgrade tested)

### Deployment
- [ ] Works in the local Docker environment
- [ ] Environment variables documented in `.env.example` if new ones were added

---

## Screenshots / Notes

<!-- Optional: Add screenshots for UI changes, or any notes for the reviewer. -->