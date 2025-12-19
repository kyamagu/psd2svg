"""Resource limits for DoS prevention.

This module provides configurable resource limits to prevent denial-of-service
attacks from malicious or malformed input files.
"""

import os
from dataclasses import dataclass


@dataclass
class ResourceLimits:
    """Resource limits for PSD conversion operations.

    These limits help prevent denial-of-service attacks by constraining:
    - File size (prevents memory exhaustion)
    - Conversion timeout (prevents CPU exhaustion)
    - Layer depth (prevents exponential processing time)
    - Image dimensions (prevents memory exhaustion from large images)

    Limits can be configured via environment variables or constructor parameters.
    Constructor parameters take precedence over environment variables.

    Environment variables:
        PSD2SVG_MAX_FILE_SIZE: Maximum file size in bytes (default: 2147483648 = 2GB)
        PSD2SVG_TIMEOUT: Conversion timeout in seconds (default: 300 = 5 minutes)
        PSD2SVG_MAX_LAYER_DEPTH: Maximum layer nesting depth (default: 100)
        PSD2SVG_MAX_IMAGE_DIMENSION: Maximum image dimension in pixels
            (default: 16383 = WebP limit)

    Example:
        >>> # Use default limits
        >>> limits = ResourceLimits.default()
        >>>
        >>> # Customize limits
        >>> limits = ResourceLimits(
        ...     max_file_size=50 * 1024 * 1024,  # 50MB
        ...     timeout=30,  # 30 seconds
        ...     max_layer_depth=50,
        ...     max_image_dimension=8192
        ... )
        >>>
        >>> # Disable specific limits (set to 0 or None)
        >>> limits = ResourceLimits(max_file_size=0)  # No file size limit
    """

    max_file_size: int = 2147483648  # 2GB default (typical for professional PSD files)
    timeout: int = 300  # 300 seconds (5 minutes) default
    max_layer_depth: int = 100  # 100 levels default
    max_image_dimension: int = 16383  # 16383 pixels default (WebP hard limit)

    @classmethod
    def default(cls) -> "ResourceLimits":
        """Create ResourceLimits with default values from environment variables.

        Returns:
            ResourceLimits instance with values from environment variables,
            falling back to hardcoded defaults if not set.
        """
        return cls(
            max_file_size=int(
                os.environ.get("PSD2SVG_MAX_FILE_SIZE", 2147483648)  # 2GB
            ),
            timeout=int(os.environ.get("PSD2SVG_TIMEOUT", 300)),  # 5 minutes
            max_layer_depth=int(os.environ.get("PSD2SVG_MAX_LAYER_DEPTH", 100)),
            max_image_dimension=int(
                os.environ.get("PSD2SVG_MAX_IMAGE_DIMENSION", 16383)  # WebP limit
            ),
        )

    @classmethod
    def unlimited(cls) -> "ResourceLimits":
        """Create ResourceLimits with all limits disabled.

        Returns:
            ResourceLimits instance with all limits set to 0 (disabled).

        Warning:
            Only use this for trusted input files in controlled environments.
        """
        return cls(
            max_file_size=0,
            timeout=0,
            max_layer_depth=0,
            max_image_dimension=0,
        )

    def is_file_size_limited(self) -> bool:
        """Check if file size limit is enabled."""
        return self.max_file_size > 0

    def is_timeout_enabled(self) -> bool:
        """Check if timeout is enabled."""
        return self.timeout > 0

    def is_layer_depth_limited(self) -> bool:
        """Check if layer depth limit is enabled."""
        return self.max_layer_depth > 0

    def is_image_dimension_limited(self) -> bool:
        """Check if image dimension limit is enabled."""
        return self.max_image_dimension > 0
