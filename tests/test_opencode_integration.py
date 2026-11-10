import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HARNESS_DIR = Path(__file__).resolve().parent / "opencode"
HARNESS_SCRIPT = HARNESS_DIR / "harness.ts"

# V1 tools live in integration/opencode/, the V2 plugin in integration/opencode-v2/.
# Both expose the same tool contract, so every behavioural test runs against both.
BACKENDS = ["v1", "v2"]

FIXTURES = {
    "tiny.xml": "<root><item id=\"a\"/><item id=\"b\"/></root>\n",
    "tiny.xsd": (
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">\n"
        "  <xs:element name=\"root\">\n"
        "    <xs:complexType>\n"
        "      <xs:sequence>\n"
        "        <xs:element name=\"item\" maxOccurs=\"unbounded\">\n"
        "          <xs:complexType>\n"
        "            <xs:attribute name=\"id\" type=\"xs:string\"/>\n"
        "          </xs:complexType>\n"
        "        </xs:element>\n"
        "      </xs:sequence>\n"
        "    </xs:complexType>\n"
        "  </xs:element>\n"
        "</xs:schema>\n"
    ),
    "malformed.xml": "<root><unclosed></root>\n",
    "wrong-elem.xml": "<wrong/>\n",
}

EXPECTED_TOOL_NAMES = {"xml_query", "xml_transform", "xml_validate"}

V2_PACKAGE_JSON = HARNESS_DIR.parent.parent / "integration" / "opencode-v2" / "package.json"
HARNESS_PACKAGE_JSON = HARNESS_DIR / "package.json"

pytestmark = pytest.mark.skipif(
    shutil.which("bun") is None,
    reason="bun runtime not available",
)


def install_harness_dependencies():
    if (HARNESS_DIR / "node_modules").exists():
        return
    install = subprocess.run(
        ["bun", "install", "--frozen-lockfile"],
        cwd=HARNESS_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if install.returncode != 0:
        pytest.fail(f"bun install failed in {HARNESS_DIR}:\n{install.stderr}")


@pytest.fixture(scope="module", params=BACKENDS)
def harness_run(request, tmp_path_factory):
    """Run the bun harness once per backend against fresh fixture files.

    The harness runs with an isolated TMPDIR so tests can assert that inline
    stylesheets do not leak temporary files.
    """
    backend = request.param
    root = tmp_path_factory.mktemp(f"opencode-{backend}")
    fixture_dir = root / "fixtures"
    fixture_dir.mkdir()
    temp_dir = root / "tmp"
    temp_dir.mkdir()

    for name, content in FIXTURES.items():
        (fixture_dir / name).write_text(content, encoding="utf-8")

    install_harness_dependencies()

    run = subprocess.run(
        ["bun", HARNESS_SCRIPT.name, str(fixture_dir), backend],
        cwd=HARNESS_DIR,
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "TMPDIR": str(temp_dir), "TEMP": str(temp_dir), "TMP": str(temp_dir)},
    )
    if run.returncode != 0:
        pytest.fail(
            f"{backend} tool harness failed:\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
        )

    entries = [json.loads(line) for line in run.stdout.splitlines() if line.strip()]
    metadata = next(entry for entry in entries if entry["type"] == "meta")
    results = {entry["case"]: entry["result"] for entry in entries if entry["type"] == "case"}

    return {
        "backend": backend,
        "stderr": run.stderr,
        "results": results,
        "metadata": metadata,
        "temp_files": sorted(path.name for path in temp_dir.iterdir()),
    }


def described_plugin_version(package_json_path, dependency_name):
    package = json.loads(package_json_path.read_text(encoding="utf-8"))
    return package["dependencies"][dependency_name]


class TestOpencodeHarnessDependencies:
    def test_v2_plugin_sdk_version_matches_harness(self):
        """The harness must exercise the same SDK version the plugin declares,
        otherwise a V2 API change could go unnoticed."""
        assert described_plugin_version(V2_PACKAGE_JSON, "@opencode/plugin") == described_plugin_version(
            HARNESS_PACKAGE_JSON, "@opencode/plugin"
        )


class TestOpencodeToolProcess:
    def test_tool_process_stderr_is_empty(self, harness_run):
        """Regression: child stderr must be captured by the tool, never leak to the
        parent process stderr (which corrupts the opencode TUI until restart)."""
        assert harness_run["stderr"] == ""

    def test_no_case_threw(self, harness_run):
        thrown = [
            name for name, result in harness_run["results"].items() if result.startswith("THREW:")
        ]
        assert thrown == []

    def test_all_tools_are_exposed_with_descriptions(self, harness_run):
        metadata = harness_run["metadata"]
        assert set(metadata["tools"]) == EXPECTED_TOOL_NAMES
        for name, description in metadata["descriptions"].items():
            assert description, f"{name} is missing a description"


class TestOpencodeQuery:
    def test_invalid_xml_returns_clean_error(self, harness_run):
        result = harness_run["results"]["query invalid xml"]
        assert result.startswith("Error (exit code 2): Invalid XML:")
        assert "Traceback" not in result

    def test_missing_file_returns_clean_error(self, harness_run):
        result = harness_run["results"]["query missing file"]
        assert result.startswith("Error (exit code 2): File not found:")

    def test_empty_xpath_rejected_without_subprocess(self, harness_run):
        assert harness_run["results"]["query empty xpath"] == "Error: xpath is required"

    def test_missing_file_argument_rejected(self, harness_run):
        assert harness_run["results"]["query missing xmlFile"] == "Error: xmlFile is required"

    def test_success(self, harness_run):
        assert harness_run["results"]["query success"] == "a\nb"


class TestOpencodeTransform:
    def test_invalid_stylesheet_returns_clean_error(self, harness_run):
        result = harness_run["results"]["transform invalid stylesheet"]
        assert result.startswith("Error (exit code 2): Invalid XSLT stylesheet:")
        assert "Traceback" not in result

    def test_success_with_params(self, harness_run):
        assert harness_run["results"]["transform success with params"] == "P-a\nP-b"

    def test_missing_stylesheet_argument_rejected(self, harness_run):
        assert (
            harness_run["results"]["transform missing stylesheet"]
            == "Error: stylesheet is required"
        )

    def test_missing_file_argument_rejected(self, harness_run):
        assert harness_run["results"]["transform missing xmlFile"] == "Error: xmlFile is required"

    def test_inline_stylesheet_leaves_no_temp_files(self, harness_run):
        leftovers = [name for name in harness_run["temp_files"] if name.endswith(".xsl")]
        assert leftovers == []


class TestOpencodeValidate:
    def test_malformed_xml_returns_clean_error(self, harness_run):
        result = harness_run["results"]["validate malformed xml"]
        assert result.startswith("Error (exit code 2): Invalid XML:")
        assert "Traceback" not in result

    def test_schema_violation_includes_error_log(self, harness_run):
        result = harness_run["results"]["validate schema violation"]
        assert result.startswith("Error (exit code 2): XML validation failed:")
        assert "No matching global declaration" in result

    def test_success(self, harness_run):
        assert harness_run["results"]["validate success"] == "Validation passed"

    def test_missing_schema_argument_rejected(self, harness_run):
        assert harness_run["results"]["validate missing schema"] == "Error: schema is required"

    def test_missing_file_argument_rejected(self, harness_run):
        assert harness_run["results"]["validate missing xmlFile"] == "Error: xmlFile is required"
