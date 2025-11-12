# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Unity MCP Server seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please Do Not:
- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed

### Please Do:
1. **Email us** at security@dexatron.com with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

2. **Allow time** for us to respond:
   - We'll acknowledge receipt within 48 hours
   - We'll provide a detailed response within 7 days
   - We'll work with you to understand and address the issue

3. **Keep it confidential** until we've released a fix

## Security Best Practices for Users

### API Keys
- **Never commit API keys** to version control
- Use environment variables (`.env` file)
- Rotate keys regularly
- Use different keys for development and production

### Dependencies
- Keep dependencies up to date: `uv sync`
- Review security advisories: `uv pip check`
- Monitor GitHub security alerts

### Data Storage
- Protect your `./data` directory (contains embeddings)
- Secure your `./downloads` directory
- Don't expose SQLite databases publicly
- Use proper file permissions

### MCP Server
- Run in isolated environments when possible
- Don't expose the server to untrusted networks
- Monitor logs for suspicious activity
- Use firewall rules appropriately

## Known Security Considerations

### OpenAI API Key
Your OpenAI API key is used for:
- Generating text embeddings
- This incurs costs on your OpenAI account
- **Secure this key carefully**

### Local Data
The server stores:
- Documentation content in SQLite
- Vector embeddings in ChromaDB
- These are stored locally in `./data`
- Ensure proper access controls

### MCP Protocol
- The server uses stdio for MCP communication
- Only runs when explicitly started
- Doesn't open network ports by default
- Logs to stderr and files (not stdout)

## Security Updates

We will:
- Release security patches as soon as possible
- Notify users via GitHub Security Advisories
- Document fixes in CHANGELOG.md
- Credit security researchers (with permission)

## Disclosure Policy

- Security issues are fixed privately
- Releases include security fix details
- CVEs assigned when appropriate
- Public disclosure after fix is released

## Contact

- **Security Issues:** security@dexatron.com
- **General Issues:** GitHub Issues
- **Questions:** GitHub Discussions

Thank you for helping keep Unity MCP Server secure! 🔒
