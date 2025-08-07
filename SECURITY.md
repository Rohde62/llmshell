## Security Policy

### Supported Versions

We actively support the following versions of LLMShell:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

### Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in LLMShell, please follow these steps:

#### 📧 Private Disclosure
**Do NOT create a public GitHub issue for security vulnerabilities.**

Instead, please report security issues privately by:
1. Emailing us directly (replace with your security contact email)
2. Using GitHub's private vulnerability reporting feature

#### 📋 What to Include
When reporting a vulnerability, please include:

- **Description**: Clear description of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Impact**: Potential impact of the vulnerability
- **Environment**: OS, Python version, LLMShell version
- **Proof of Concept**: If available, a minimal PoC (without causing harm)

#### ⏰ Response Timeline
- **Acknowledgment**: Within 24 hours
- **Initial Assessment**: Within 72 hours
- **Status Updates**: Weekly until resolved
- **Fix Timeline**: Varies by severity (critical: 1-7 days, high: 1-30 days)

#### 🔒 Security Best Practices

When using LLMShell:

1. **Keep Updated**: Always use the latest version
2. **Secure Configuration**: Review configuration files for sensitive data
3. **Network Security**: Be cautious when using LLM APIs over networks
4. **Input Validation**: Be aware that LLMShell executes shell commands
5. **Permissions**: Run with minimal necessary permissions
6. **Audit**: Regularly review command history and logs

#### 🚨 Known Security Considerations

- **Command Execution**: LLMShell executes shell commands - review output before execution
- **API Keys**: Store LLM API keys securely, never commit to version control
- **Network Traffic**: LLM API calls may transmit your commands over the network
- **Command History**: Commands are stored locally - protect your history files

#### 🏆 Security Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

<!-- Future contributors will be listed here -->

Thank you for helping keep LLMShell secure!
