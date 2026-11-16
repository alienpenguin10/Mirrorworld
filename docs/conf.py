# Sphinx configuration for the mirrorworld documentation.
# Build locally:  pip install -r docs/requirements.txt && sphinx-build -b html docs docs/_build/html
import os
import re
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "mirrorworld"
author = "alienpenguin10, based on streetlevel by skzk"
copyright = "2022-2026, skzk and alienpenguin10"
release = re.search(r'__version__ = "(.+)"', open(os.path.join("..", "mirrorworld", "__init__.py")).read()).group(1)
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_design",
    "sphinx_copybutton",
]

myst_enable_extensions = ["colon_fence", "deflist", "attrs_inline", "attrs_block", "html_image", "fieldlist"]
myst_heading_anchors = 3
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", "build", "scripts", "Thumbs.db", ".DS_Store"]
templates_path = ["_templates"]

autodoc_typehints = "description"
autodoc_member_order = "bysource"
add_module_names = False
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
copybutton_prompt_text = r">>> |\$ "
copybutton_prompt_is_regexp = True

html_theme = "furo"
html_title = f"mirrorworld {release}"
html_logo = "_static/logo.svg"
html_favicon = "_static/logo.svg"
html_static_path = ["_static"]
html_css_files = ["css/additional.css", "css/mirrorworld.css"]
html_show_sourcelink = False
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "source_repository": "https://github.com/alienpenguin10/Mirrorworld/",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {
        "color-brand-primary": "#5b4bdb",
        "color-brand-content": "#5b4bdb",
        "color-admonition-background": "#f5f4ff",
        "font-stack": "Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
    },
    "dark_css_variables": {
        "color-brand-primary": "#a99cff",
        "color-brand-content": "#a99cff",
        "color-background-primary": "#0f1117",
        "color-background-secondary": "#151823",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/alienpenguin10/Mirrorworld",
            "html": '<svg stroke="currentColor" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" '
                    'd="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49'
                    '-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23'
                    '.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15'
                    '-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2'
                    '-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73'
                    '.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>',
            "class": "",
        },
    ],
}
