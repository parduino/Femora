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
SSI_VTK_SOURCE = os.path.join(WEBSITE_DIR, "ssi-source", "scene.vtk")
SSI_EXPORT_SCRIPT = os.path.join(ROOT_DIR, "scripts", "export_ssi_viewer.py")
PORT = 8000


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


def build_ssi_viewer():
    """Export the SSI viewer from the canonical VTK source file."""
    if not os.path.exists(SSI_VTK_SOURCE):
        print(f"ERROR: SSI source mesh not found at {SSI_VTK_SOURCE}.")
        sys.exit(1)

    if not os.path.exists(SSI_EXPORT_SCRIPT):
        print(f"ERROR: SSI export script not found at {SSI_EXPORT_SCRIPT}.")
        sys.exit(1)

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


def build_mkdocs():
    """Build MkDocs into the docs subfolder of the test site."""
    print_step("Building Documentation")

    mkdocs_config = os.path.join(WEBSITE_DIR, "mkdocs.yml")
    output_dir = os.path.join(TEST_DIR, "docs")
    cmd = [
        "mkdocs",
        "build",
        "--config-file",
        mkdocs_config,
        "--site-dir",
        output_dir,
    ]

    try:
        subprocess.run(cmd, shell=True, check=True)
        print("Documentation built successfully.")
    except subprocess.CalledProcessError:
        print("MkDocs build failed.")
        sys.exit(1)


def serve():
    """Serve the final combined site."""
    print_step(f"Launching Server at http://localhost:{PORT}")

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


if __name__ == "__main__":
    check_prerequisites()
    install_node_deps()
    build_ssi_viewer()
    build_nextjs()
    prepare_test_folder()
    build_mkdocs()
    serve()
