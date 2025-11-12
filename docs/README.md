# Documentation

This directory contains the Sphinx documentation for psd2svg.

## Building Documentation

### Install Dependencies

```bash
uv sync --group docs
```

### Build HTML Documentation

```bash
uv run sphinx-build -b html docs docs/_build/html
```

The generated HTML files will be in `docs/_build/html/`. Open `docs/_build/html/index.html` in your browser to view the documentation.

### Build with Warnings as Errors

```bash
uv run sphinx-build -b html docs docs/_build/html -W
```

## Documentation Structure

- `index.rst` - Main landing page
- `getting-started.rst` - Installation and quick start guide
- `user-guide.rst` - Detailed usage documentation
- `api-reference.rst` - Auto-generated API documentation
- `rasterizers.rst` - Rasterizer backends guide
- `development.rst` - Development and contribution guide
- `limitations.rst` - Known limitations and workarounds
- `changelog.rst` - Version history
- `conf.py` - Sphinx configuration
- `examples/` - Code examples
- `_static/` - Custom CSS and static files
- `_templates/` - Custom Sphinx templates

## Contributing

When adding new documentation:

1. Create `.rst` files in the `docs/` directory
2. Add them to the appropriate `toctree` in `index.rst`
3. Build and verify the documentation
4. Commit both the source `.rst` files (not the built HTML)
