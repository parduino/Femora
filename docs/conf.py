# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
import shutil

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../src'))
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'FEMORA (Fast Efficient Meshing for OpenSees-based Resilience Analysis)'
copyright = '2025, Amin Pakzad'
author = 'Amin Pakzad'
release = '0.5.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- autodoc configuration ---------------------------------------------------
# Use custom template for autoclass directive
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'special-members': '__init__',
}

# Mock imports for modules that might not be available during documentation building
autodoc_mock_imports = ['pykdtree']

# Set custom templates
autodoc_class_template = 'autoclasstemplate.rst'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']



# Custom function to copy the entire images directory structure to the build output
def setup(app):
    # Source and destination directories
    images_src_dir = os.path.join(app.srcdir, 'images')
    images_dst_dir = os.path.join(app.outdir, 'images')
    
    # Copy the entire images directory tree recursively
    if os.path.exists(images_src_dir):
        if os.path.exists(images_dst_dir):
            shutil.rmtree(images_dst_dir)
        shutil.copytree(images_src_dir, images_dst_dir)
    
    # Copy the introduction/images directory and its contents
    intro_images_src_dir = os.path.join(app.srcdir, 'introduction', 'images')
    intro_images_dst_dir = os.path.join(app.outdir, 'introduction', 'images')
    
    # Create the introduction directory if it doesn't exist
    intro_dir = os.path.join(app.outdir, 'introduction')
    if not os.path.exists(intro_dir):
        os.makedirs(intro_dir)
    
    # Copy the entire introduction/images directory tree recursively
    if os.path.exists(intro_images_src_dir):
        if os.path.exists(intro_images_dst_dir):
            shutil.rmtree(intro_images_dst_dir)
        shutil.copytree(intro_images_src_dir, intro_images_dst_dir)
    
    return app

# -- Custom CSS ----------------------------------------------------------
html_css_files = [
    'css/custom.css',
]

# -- Custom JavaScript files ------------------------------------------------
html_js_files = [
    'js/copy-button.js',
]

# -- Logo configuration -----------------------------------------------------
html_logo = 'images/Femoralogo.png'
html_theme_options = {
    'logo_only': True,
}
