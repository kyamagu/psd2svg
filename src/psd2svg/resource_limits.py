"""Resource limits for DoS prevention.

This module provides configurable resource limits to prevent denial-of-service
attacks from malicious or malformed input files.
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# WebP hard limit for image dimensions (16383 pixels)
WEBP_MAX_DIMENSION = 16383


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
        PSD2SVG_TIMEOUT: Conversion timeout in seconds (default: 180 = 3 minutes)
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
    timeout: int = 180  # 180 seconds (3 minutes) default
    max_layer_depth: int = 100  # 100 levels default
    max_image_dimension: int = WEBP_MAX_DIMENSION  # WebP hard limit

    @classmethod
    def default(cls) -> "ResourceLimits":
        """Create ResourceLimits with default values from environment variables.

        Returns:
            ResourceLimits instance with values from environment variables,
            falling back to hardcoded defaults if not set.

        Raises:
            ValueError: If environment variable contains invalid integer value.

        Note:
            Negative values are treated as 0 (disabled limit) with a warning logged.
            Non-integer values raise ValueError. For intentionally disabling all
            limits, use ResourceLimits.unlimited() instead of negative values.
        """

        def parse_env_int(key: str, default: int) -> int:
            """Parse integer from environment variable with validation.

            Args:
                key: Environment variable name.
                default: Default value if not set.

            Returns:
                Parsed integer value, or 0 if negative.

            Raises:
                ValueError: If value is not a valid integer.
            """
            value_str = os.environ.get(key)
            if value_str is None:
                return default

            try:
                value = int(value_str)
            except ValueError as e:
                raise ValueError(
                    f"Environment variable {key}={value_str!r} is not a valid integer"
                ) from e

            # Treat negative values as 0 (disabled limit)
            if value < 0:
                logger.warning(
                    f"Environment variable {key}={value} is negative, "
                    f"treating as 0 (disabled limit). "
                    f"Consider using ResourceLimits.unlimited() instead."
                )
                return 0

            return value

        return cls(
            max_file_size=parse_env_int("PSD2SVG_MAX_FILE_SIZE", 2147483648),  # 2GB
            timeout=parse_env_int("PSD2SVG_TIMEOUT", 180),  # 3 minutes
            max_layer_depth=parse_env_int("PSD2SVG_MAX_LAYER_DEPTH", 100),
            max_image_dimension=parse_env_int(
                "PSD2SVG_MAX_IMAGE_DIMENSION",
                WEBP_MAX_DIMENSION,
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
