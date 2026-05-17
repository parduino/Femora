import argparse
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import webbrowser

# --- CONFIGURATION ---
ROOT_DIR = os.getcwd()
WEBSITE_DIR = os.path.join(ROOT_DIR, "website")
TEST_DIR = os.path.join(ROOT_DIR, "_local_test")
NEXTJS_BUILD_OUTPUT = os.path.join(WEBSITE_DIR, "out")
ZENSICAL_BUILD_OUTPUT = os.path.join(WEBSITE_DIR, "site")
ZENSICAL_CONFIG = os.path.join(WEBSITE_DIR, "mkdocs-zensical.yml")
ZENSICAL_DOCS_SOURCE = os.path.join(WEBSITE_DIR, "zensical_preview_docs")
ZENSICAL_REF_SCRIPT = os.path.join(WEBSITE_DIR, "build_zensical_reference.py")
SSI_VTK_SOURCE = os.path.join(WEBSITE_DIR, "ssi-source", "scene.vtk")
SSI_EXPORT_SCRIPT = os.path.join(ROOT_DIR, "scripts", "export_ssi_viewer.py")
SSI_EXPORT_HTML = os.path.join(WEBSITE_DIR, "public", "ssi-viewer", "index.html")
PORT = 8000
NEXT_DEV_PORT = 3000


def print_step(message):
    print(f"\n{'=' * 60}")
    print(f"> {message}")
    print(f"{'=' * 60}")


def check_prerequisites():
    """Check whether static export is configured in Next.js."""
    config_path = os.path.join(WEBSITE_DIR, "next.config.mjs")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "output: 'export'" not in content and 'output: "export"' not in content:
                print("ERROR: next.config.mjs is missing `output: 'export'`.")
                print("Add it to the config object so Next.js creates HTML files.")
                sys.exit(1)


def install_node_deps():
    """Install npm packages if node_modules is missing."""
    node_modules = os.path.join(WEBSITE_DIR, "node_modules")
    if not os.path.exists(node_modules):
        print_step("Installing Node.js dependencies")
        subprocess.run("npm install", cwd=WEBSITE_DIR, shell=True, check=True)
    else:
        print("Node modules already installed.")


def _mtime(path):
    return os.path.getmtime(path) if os.path.exists(path) else None


def ssi_export_needed():
    """Return True when the SSI viewer should be regenerated."""
    if not os.path.exists(SSI_EXPORT_HTML):
        return True

    export_time = _mtime(SSI_EXPORT_HTML)
    source_time = _mtime(SSI_VTK_SOURCE)
    script_time = _mtime(SSI_EXPORT_SCRIPT)

    return export_time is None or source_time is None or script_time is None or export_time < max(source_time, script_time)


def build_ssi_viewer(force=False):
    """Export the SSI viewer from the canonical VTK source file."""
    if not os.path.exists(SSI_VTK_SOURCE):
        print(f"ERROR: SSI source mesh not found at {SSI_VTK_SOURCE}.")
        sys.exit(1)

    if not os.path.exists(SSI_EXPORT_SCRIPT):
        print(f"ERROR: SSI export script not found at {SSI_EXPORT_SCRIPT}.")
        sys.exit(1)

    if not force and not ssi_export_needed():
        print("SSI viewer is up to date. Skipping export.")
        return

    print_step("Exporting SSI Viewer")

    cmd = [
        sys.executable,
        SSI_EXPORT_SCRIPT,
        "--vtk",
        SSI_VTK_SOURCE,
        "--title",
        "Femora SSI model",
    ]

    try:
        subprocess.run(cmd, check=True)
        print("SSI viewer exported successfully.")
    except subprocess.CalledProcessError:
        print("SSI viewer export failed.")
        sys.exit(1)


def build_nextjs():
    """Build the Next.js website into static HTML."""
    print_step("Building Next.js Landing Page")

    try:
        subprocess.run("npm run build", cwd=WEBSITE_DIR, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("Next.js build failed.")
        print("Run `npm run build` inside the website folder to see the error.")
        sys.exit(1)

    if not os.path.exists(NEXTJS_BUILD_OUTPUT):
        print(f"ERROR: The `out` folder was not created at {NEXTJS_BUILD_OUTPUT}.")
        sys.exit(1)


def prepare_test_folder():
    """Copy the Next.js build to the local test folder."""
    print_step("Preparing Local Test Folder")

    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

    shutil.copytree(NEXTJS_BUILD_OUTPUT, TEST_DIR)
    print(f"Website copied to {TEST_DIR}")


def build_docs(engine="mkdocs"):
    """Build documentation into the docs subfolder of the test site."""
    mkdocs_config = os.path.join(WEBSITE_DIR, "mkdocs.yml")
    output_dir = os.path.join(TEST_DIR, "docs")

    print_step(f"Building Documentation ({engine})")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    if engine == "mkdocs":
        build_mkdocs_site(mkdocs_config, output_dir)
        print("Documentation built successfully with MkDocs.")
        return

    if engine == "zensical":
        if os.path.exists(ZENSICAL_BUILD_OUTPUT):
            shutil.rmtree(ZENSICAL_BUILD_OUTPUT)

        prepare_zensical_docs_source()

        cmd = [
            "zensical",
            "build",
            "--config-file",
            os.path.basename(ZENSICAL_CONFIG),
            "--clean",
        ]
        try:
            subprocess.run(cmd, cwd=WEBSITE_DIR, shell=True, check=True)
        except subprocess.CalledProcessError:
            print("Zensical build failed.")
            print("Make sure `zensical` is installed and compatible with the current docs config.")
            sys.exit(1)
        finally:
            cleanup_zensical_docs_source()

        if not os.path.exists(ZENSICAL_BUILD_OUTPUT):
            print(f"ERROR: Zensical did not create a site directory at {ZENSICAL_BUILD_OUTPUT}.")
            sys.exit(1)

        shutil.copytree(ZENSICAL_BUILD_OUTPUT, output_dir)
        print("Documentation built successfully with Zensical.")
        return

    print(f"ERROR: Unknown docs engine '{engine}'.")
    sys.exit(1)


def build_mkdocs_site(config_path, site_dir):
    """Build the documentation site with MkDocs into ``site_dir``."""
    cmd = [
        "mkdocs",
        "build",
        "--config-file",
        config_path,
        "--site-dir",
        site_dir,
    ]
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("MkDocs build failed.")
        sys.exit(1)


def prepare_zensical_docs_source():
    """Create a temporary docs tree with pre-generated API reference pages for Zensical."""
    if os.path.exists(ZENSICAL_DOCS_SOURCE):
        shutil.rmtree(ZENSICAL_DOCS_SOURCE)

    shutil.copytree(os.path.join(WEBSITE_DIR, "docs"), ZENSICAL_DOCS_SOURCE)

    cmd = [
        sys.executable,
        ZENSICAL_REF_SCRIPT,
        "--output-root",
        ZENSICAL_DOCS_SOURCE,
    ]
    try:
        subprocess.run(cmd, cwd=WEBSITE_DIR, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("Zensical reference prebuild failed.")
        sys.exit(1)

    reference_index = os.path.join(ZENSICAL_DOCS_SOURCE, "reference", "index.md")
    if not os.path.exists(reference_index):
        print(f"ERROR: Zensical preview docs did not include {reference_index}.")
        sys.exit(1)


def cleanup_zensical_docs_source():
    """Remove the temporary Zensical docs source tree after building."""
    if os.path.exists(ZENSICAL_DOCS_SOURCE):
        shutil.rmtree(ZENSICAL_DOCS_SOURCE)


def serve_static():
    """Serve the final combined site."""
    print_step(f"Launching Static Server at http://localhost:{PORT}")

    os.chdir(TEST_DIR)
    url = f"http://localhost:{PORT}"
    webbrowser.open(url)

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        try:
            print("(Press Ctrl+C to stop the server)")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


def run_website_dev(skip_ssi=False, force_ssi=False):
    """Run the fast Next.js dev server for landing-page work."""
    install_node_deps()
    if not skip_ssi:
        build_ssi_viewer(force=force_ssi)

    print_step(f"Launching Next.js Dev Server at http://localhost:{NEXT_DEV_PORT}")
    webbrowser.open(f"http://localhost:{NEXT_DEV_PORT}")

    try:
        subprocess.run("npm run dev", cwd=WEBSITE_DIR, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("Next.js dev server failed.")
        sys.exit(1)


def run_full_build(skip_ssi=False, force_ssi=False, docs_engine="mkdocs"):
    """Run the original full local site pipeline."""
    check_prerequisites()
    install_node_deps()
    if not skip_ssi:
        build_ssi_viewer(force=force_ssi)
    build_nextjs()
    prepare_test_folder()
    build_docs(engine=docs_engine)
    serve_static()


def parse_args():
    parser = argparse.ArgumentParser(description="Local Femora website/docs runner.")
    parser.add_argument(
        "--mode",
        choices=["full", "website"],
        default="full",
        help="`full` builds the merged static website + docs. `website` runs fast Next.js dev mode for landing-page editing.",
    )
    parser.add_argument(
        "--docs-engine",
        choices=["mkdocs", "zensical"],
        default="mkdocs",
        help="Documentation builder to use in `full` mode. Default is `mkdocs`.",
    )
    parser.add_argument(
        "--skip-ssi",
        action="store_true",
        help="Skip regenerating the SSI viewer.",
    )
    parser.add_argument(
        "--force-ssi",
        action="store_true",
        help="Force regenerating the SSI viewer even if outputs are up to date.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.mode == "website":
        run_website_dev(skip_ssi=args.skip_ssi, force_ssi=args.force_ssi)
    else:
        run_full_build(
            skip_ssi=args.skip_ssi,
            force_ssi=args.force_ssi,
            docs_engine=args.docs_engine,
        )
