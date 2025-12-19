====================
Security Considerations
====================

This guide covers security considerations when using psd2svg, especially when processing untrusted input files.

Overview
========

psd2svg processes PSD files which can contain:

- Complex layer structures
- Embedded images (potentially very large)
- Font references
- External resource references

When processing untrusted PSD files, you should be aware of potential security risks and implement appropriate mitigations.

Security Features
=================

Path Traversal Protection
-------------------------

The ``image_prefix`` parameter in ``save()`` and ``tostring()`` methods has built-in protections:

.. code-block:: python

    from psd2svg import SVGDocument

    document = SVGDocument.from_psd(psdimage)

    # ✓ Safe: Relative paths are allowed
    document.save("output.svg", image_prefix="images/output")

    # ✗ Blocked: Path traversal attempts are rejected
    try:
        document.save("output.svg", image_prefix="../../../etc/output")
    except ValueError as e:
        print(e)  # "image_prefix cannot contain '..' (path traversal not allowed)"

    # ✗ Blocked: Absolute paths without svg_filepath are rejected
    try:
        document.tostring(image_prefix="/tmp/output")
    except ValueError as e:
        print(e)  # "image_prefix must be relative when svg_filepath is not provided"

These protections prevent malicious or compromised code from writing files outside intended directories.

Font File Validation
--------------------

When extracting font files from SVG ``@font-face`` rules (used by ResvgRasterizer), psd2svg validates:

1. **File extensions**: Only valid font formats are accepted (``.ttf``, ``.otf``, ``.woff``, ``.woff2``, ``.ttc``)
2. **File existence**: Non-existent files are skipped with a warning

.. code-block:: python

    from psd2svg.rasterizer import ResvgRasterizer

    # Font files are automatically validated
    rasterizer = ResvgRasterizer()

    # Valid font files are used, invalid ones are skipped
    image = rasterizer.from_string(svg_content)

This prevents:

- Access to arbitrary file paths (e.g., ``/etc/passwd``)
- Log pollution from invalid paths
- Potential information disclosure

Security Best Practices
=======================

Processing Untrusted Files
--------------------------

When processing PSD files from untrusted sources, implement multiple layers of defense:

1. File Size Limits
^^^^^^^^^^^^^^^^^^^

Limit input file size to prevent memory exhaustion:

.. code-block:: python

    import os
    from psd_tools import PSDImage
    from psd2svg import SVGDocument

    # Note: Professional PSD files are typically 1-5GB
    # Adjust limits based on your use case:
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB for trusted users
    # For untrusted sources:
    # MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

    def safe_convert(psd_path: str) -> SVGDocument:
        # Check file size before loading
        file_size = os.path.getsize(psd_path)
        if file_size > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})"
            )

        psdimage = PSDImage.open(psd_path)

        # Important: Validate layer dimensions to prevent WebP encoding errors
        # WebP has a hard limit of 16383 pixels per dimension
        for layer in psdimage.descendants():
            if hasattr(layer, 'width') and hasattr(layer, 'height'):
                if layer.width > 16383 or layer.height > 16383:
                    raise ValueError(
                        f"Layer '{layer.name}' exceeds WebP dimension limit: "
                        f"{layer.width}x{layer.height} (max: 16383x16383)"
                    )

        return SVGDocument.from_psd(psdimage)

2. Timeout Protection
^^^^^^^^^^^^^^^^^^^^^

Implement timeout to prevent CPU exhaustion. Large PSD files can take several minutes to process:

.. code-block:: python

    import signal
    from contextlib import contextmanager

    @contextmanager
    def timeout(seconds: int):
        """Context manager for timeout protection."""
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {seconds} seconds")

        # Set the signal handler and alarm
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def safe_convert_with_timeout(psd_path: str, timeout_seconds: int = 300):
        """Convert PSD with timeout protection.

        Note: 5 minutes (300s) is reasonable for professional PSD files.
        For untrusted input, use shorter timeouts (60-120s).
        """
        try:
            with timeout(timeout_seconds):
                psdimage = PSDImage.open(psd_path)
                return SVGDocument.from_psd(psdimage)
        except TimeoutError as e:
            print(f"Conversion timed out: {e}")
            return None

**Note**: ``signal.alarm()`` is not available on Windows. For cross-platform timeout support, use ``subprocess`` or ``threading.Timer``.

3. Sandboxing with Subprocess
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run conversion in a separate process with resource limits:

.. code-block:: python

    import subprocess
    import json
    from pathlib import Path

    def convert_sandboxed(
        psd_path: str,
        output_path: str,
        timeout: int = 60,
        max_memory_mb: int = 512
    ) -> bool:
        """Convert PSD in sandboxed subprocess."""
        script = f"""
    from psd_tools import PSDImage
    from psd2svg import SVGDocument

    psdimage = PSDImage.open({psd_path!r})
    document = SVGDocument.from_psd(psdimage)
    document.save({output_path!r})
    """

        try:
            # Run in subprocess with timeout
            result = subprocess.run(
                ["python", "-c", script],
                timeout=timeout,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"Conversion failed: {result.stderr}")
                return False

            return True

        except subprocess.TimeoutExpired:
            print(f"Conversion timed out after {timeout} seconds")
            return False
        except Exception as e:
            print(f"Conversion error: {e}")
            return False

4. Container Isolation
^^^^^^^^^^^^^^^^^^^^^^

For maximum isolation, run conversions in Docker containers:

.. code-block:: bash

    # Dockerfile
    FROM python:3.10-slim
    RUN pip install psd2svg
    WORKDIR /workspace

    # Run with resource limits
    docker run --rm \
        --memory=512m \
        --cpus=1 \
        --network=none \
        -v /path/to/input:/input:ro \
        -v /path/to/output:/output:rw \
        psd2svg-image \
        python -m psd2svg /input/file.psd /output/file.svg

Path Validation
---------------

Always validate user-provided paths:

.. code-block:: python

    import os
    from pathlib import Path

    def validate_path(path: str, base_dir: str) -> str:
        """Validate path is within base directory."""
        # Resolve to absolute path
        resolved = Path(path).resolve()
        base = Path(base_dir).resolve()

        # Check if path is within base directory
        try:
            resolved.relative_to(base)
        except ValueError:
            raise ValueError(f"Path {path} is outside base directory {base_dir}")

        return str(resolved)

    # Usage
    safe_output = validate_path(user_provided_path, "/safe/output/dir")

Font Security
-------------

When using custom fonts or font embedding:

.. code-block:: python

    from pathlib import Path

    # Define trusted font directories
    TRUSTED_FONT_DIRS = [
        "/usr/share/fonts",
        "/System/Library/Fonts",
        str(Path.home() / ".fonts"),
    ]

    def validate_font_path(font_path: str) -> bool:
        """Check if font comes from trusted directory."""
        resolved = Path(font_path).resolve()
        return any(
            str(resolved).startswith(trusted_dir)
            for trusted_dir in TRUSTED_FONT_DIRS
        )

    # Usage
    if not validate_font_path(font_file):
        raise ValueError("Untrusted font file")

Known Limitations
=================

Resource Consumption
--------------------

PSD processing can be resource-intensive:

- **Memory**: Large PSD files or many embedded images can consume significant memory
- **CPU**: Complex layer effects and deeply nested layers require substantial processing
- **Disk**: Output SVG files with embedded images can be very large

**Impact**: Can lead to denial of service if not properly limited.

**Mitigation**:

- Implement file size limits before processing (2GB for trusted, 500MB for untrusted)
- Use timeouts for conversion operations (5 minutes for trusted, 1-2 minutes for untrusted)
- Run in resource-constrained environments
- Monitor resource usage in production

WebP Dimension Limits
---------------------

**Critical Limitation**: WebP format has a hard limit of **16383 pixels per dimension**.

This is a common issue with professional Photoshop files that contain:

- High-resolution print designs (e.g., 300 DPI posters)
- Large billboard or banner designs
- Detailed panoramic images
- Individual layers exceeding 16383 pixels on either width or height

**Impact**: Conversion will fail with a WebP encoding error when encountering oversized layers.

**Error Example**::

    PIL.Image.DecompressionBombError: Image size exceeds limit
    # or
    OSError: cannot write mode RGBA as WEBP

**Recommended Mitigations**:

1. **Pre-validate layer dimensions** (see File Size Limits example above)
2. **Use alternative image formats** for large layers:

   .. code-block:: python

       # Save with PNG format for layers that might exceed WebP limits
       document.save("output.svg", image_format="PNG")

3. **Downscale large layers** before conversion (if quality loss is acceptable)
4. **Rasterize the entire PSD** instead of per-layer conversion for very large files

**Note**: This is a fundamental WebP format limitation, not a psd2svg limitation. PNG format supports up to 2^31-1 pixels per dimension and can be used as an alternative.

External Dependencies
---------------------

psd2svg depends on several libraries:

- ``psd-tools``: PSD file parsing
- ``fonttools``: Font handling
- ``pillow``: Image processing
- ``resvg-py``: SVG rasterization (default)
- ``playwright``: Browser-based rasterization (optional)

**Impact**: Vulnerabilities in dependencies could affect psd2svg.

**Mitigation**:

- Automated security scanning via Dependabot and GitHub Actions
- Regular dependency updates
- See ``SECURITY.md`` for vulnerability reporting

SVG Output Security
-------------------

Generated SVG files may contain:

- Embedded images (data URIs)
- Font data (data URIs)
- External resource references

**Impact**: SVG files rendered in browsers could potentially exploit browser vulnerabilities.

**Mitigation**:

- Sanitize SVG output before rendering in untrusted contexts
- Use Content Security Policy (CSP) when serving SVG files
- Consider server-side rendering for untrusted content

Security Checklist
==================

When deploying psd2svg in production:

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Priority
     - Recommendation
   * - High
     - ✓ Implement file size limits for input files
   * - High
     - ✓ Implement timeout protection for conversions
   * - High
     - ✓ Validate all user-provided file paths
   * - High
     - ✓ Keep dependencies up to date
   * - Medium
     - ✓ Run conversions in sandboxed environments
   * - Medium
     - ✓ Monitor resource usage (CPU, memory, disk)
   * - Medium
     - ✓ Validate font file sources
   * - Medium
     - ✓ Implement rate limiting for conversion APIs
   * - Low
     - ✓ Use container isolation for maximum security
   * - Low
     - ✓ Sanitize SVG output for web rendering

Security Updates
================

Security features and fixes are documented in the changelog. Subscribe to:

- **GitHub Security Advisories**: https://github.com/kyamagu/psd2svg/security/advisories
- **Release Notes**: https://github.com/kyamagu/psd2svg/releases
- **Dependabot Alerts**: Enable for your repository

Reporting Security Issues
=========================

See ``SECURITY.md`` in the repository root for instructions on reporting security vulnerabilities.

Additional Resources
====================

- `SECURITY.md <https://github.com/kyamagu/psd2svg/blob/main/SECURITY.md>`_ - Security policy
- `OWASP Secure Coding Practices <https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/>`_
- `CWE Top 25 <https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html>`_
