# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

We recommend always using the latest version of psd2svg to ensure you have the latest security updates.

## Reporting a Vulnerability

We take the security of psd2svg seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Create a Public Issue

Please **do not** create a public GitHub issue for security vulnerabilities. Public disclosure before a fix is available can put users at risk.

### 2. Report Privately

Report security vulnerabilities by opening a [GitHub Security Advisory](https://github.com/kyamagu/psd2svg/security/advisories/new).

Alternatively, you can email the maintainer directly. Check the repository for contact information.

### 3. Provide Details

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Impact**: What an attacker could do if they exploit this vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the vulnerability
- **Proof of Concept**: Code or files demonstrating the vulnerability (if applicable)
- **Suggested Fix**: If you have ideas for how to fix the issue (optional)
- **Your Information**: How we can contact you for follow-up questions

### 4. Response Timeline

- **Initial Response**: We aim to acknowledge your report within 48 hours
- **Status Updates**: We will provide status updates at least every 7 days
- **Fix Timeline**: We aim to release a fix within 30 days for critical vulnerabilities
- **Disclosure**: We will coordinate with you on the disclosure timeline

## Security Best Practices for Users

When using psd2svg, especially with untrusted input files, follow these best practices:

### 1. Input Validation

```python
import os
from psd_tools import PSDImage
from psd2svg import SVGDocument

# Check file size before processing
# Note: Professional PSD files are often 1-5GB; adjust based on your use case
max_size = 2 * 1024 * 1024 * 1024  # 2GB for trusted users
# For untrusted sources, use more restrictive limits:
# max_size = 500 * 1024 * 1024  # 500MB for untrusted input

if os.path.getsize(psd_path) > max_size:
    raise ValueError(f"File too large: {os.path.getsize(psd_path)} bytes")

# Important: Check layer dimensions to prevent WebP encoding errors
psdimage = PSDImage.open(psd_path)
for layer in psdimage.descendants():
    if hasattr(layer, 'width') and hasattr(layer, 'height'):
        # WebP has a hard limit of 16383 pixels per dimension
        if layer.width > 16383 or layer.height > 16383:
            raise ValueError(
                f"Layer '{layer.name}' exceeds WebP dimension limit: "
                f"{layer.width}x{layer.height} (max: 16383x16383)"
            )

document = SVGDocument.from_psd(psdimage)
```

### 2. Sandboxing

When processing untrusted PSD files, consider running the conversion in a sandboxed environment:

- Use containers (Docker) with resource limits
- Run in a separate process with timeout
- Limit file system access

```python
import subprocess
import signal

def convert_with_timeout(psd_path, svg_path, timeout=60):
    """Convert PSD to SVG with timeout."""
    try:
        proc = subprocess.run(
            ["python", "-m", "psd2svg", psd_path, svg_path],
            timeout=timeout,
            capture_output=True,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Conversion timed out after {timeout} seconds")
        return False
```

### 3. File Path Validation

Always validate file paths when using the `image_prefix` parameter:

```python
import os

# Use relative paths only
image_prefix = "images/output"

# Avoid user-controlled absolute paths
# Bad: image_prefix = user_input  # Could be "/etc/passwd"

# Validate paths
if ".." in image_prefix or os.path.isabs(image_prefix):
    raise ValueError("Invalid image_prefix")
```

### 4. Font File Security

When embedding fonts, ensure font files come from trusted sources:

```python
# Only use fonts from trusted directories
trusted_font_dirs = ["/usr/share/fonts", "/System/Library/Fonts"]

# Validate font paths
from pathlib import Path
font_path = Path(font_file).resolve()
if not any(str(font_path).startswith(d) for d in trusted_font_dirs):
    raise ValueError("Untrusted font file")
```

## Known Security Considerations

### Resource Consumption

PSD files can be very large and complex. Processing untrusted PSD files may lead to:

- **Memory exhaustion**: Large embedded images or many layers
- **CPU exhaustion**: Complex layer effects or deeply nested layers
- **Disk exhaustion**: Large output SVG files with embedded images

**Mitigation**: Implement file size limits, timeouts, and run in resource-constrained environments.

### Path Traversal

The `image_prefix` parameter in `save()` and `tostring()` methods has protections against path traversal:

- Prevents `..` in paths (since version TBD)
- Validates absolute paths (since version TBD)

**Mitigation**: Always validate user-provided paths before use.

### Font File Access

When rasterizing with custom fonts, the library may access font files on the system:

- ResvgRasterizer validates font file extensions (since version TBD)
- PlaywrightRasterizer accesses fonts via Chromium

**Mitigation**: Ensure font files come from trusted sources.

## Automated Security Scanning

This project uses automated security scanning:

- **Dependabot**: Automatic dependency updates and vulnerability alerts
- **pip-audit**: Python-specific vulnerability scanning
- **Safety**: Dependency security checker
- **Trivy**: Comprehensive security scanner

Security scan results are available in the [Security tab](https://github.com/kyamagu/psd2svg/security).

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities. Contributors who report valid security issues may be acknowledged in release notes (with their permission).

## Questions?

If you have questions about this security policy, please open a discussion in the [Discussions tab](https://github.com/kyamagu/psd2svg/discussions).
