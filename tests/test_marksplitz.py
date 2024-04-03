import pytest
from marksplitz import marksplitz


def test_split_markdown_file(tmp_path):
    # Create a temporary directory with a Markdown file.
    md_file = tmp_path / "test.md"
    md_file.write_text(
        "# Test\n"
        "This is a test.\n"
        "---\n"
        "## Section 1\n"
        "This is section 1.\n"
        "---\n"
        "## Section 2\n"
        "This is section 2.\n"
    )

    # Create a temporary directory for the output.
    out_dir = tmp_path / "Output"
    out_dir.mkdir()

    # Run the main function passing the Markdown file and output directory.
    args = [str(md_file), "-o", str(out_dir)]
    marksplitz.main(args)

    # Check that the output directory contains the expected files.
    assert (out_dir / "page-001.html").exists()
    assert (out_dir / "page-002.html").exists()
    assert (out_dir / "page-003.html").exists()

    # Check that the output files contains some of the expected content.
    text1 = (out_dir / "page-001.html").read_text()
    assert "<h1>Test</h1>" in text1
    assert "<p>This is a test.</p>" in text1

    text2 = (out_dir / "page-002.html").read_text()
    assert "<h2>Section 1</h2>" in text2
    assert "<p>This is section 1.</p>" in text2

    text3 = (out_dir / "page-003.html").read_text()
    assert "<h2>Section 2</h2>" in text3
    assert "<p>This is section 2.</p>" in text3


def test_creates_default_output_directory(tmp_path):
    # Create a temporary directory with a Markdown file.
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\nThis is a test.\n")

    # Run the main function passing the Markdown file.
    marksplitz.main([str(md_file)])

    # Check that a default output directory was created.
    dirs = [p for p in list(tmp_path.iterdir()) if p.is_dir()]
    assert len(dirs) == 1
    assert dirs[0].name.startswith("Pages_")

    # Check that the output directory contains the expected file.
    assert (dirs[0] / "page-001.html").exists()


@pytest.mark.parametrize("name_option", ["-n", "--output-name"])
def test_output_name_option(tmp_path, name_option):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\nThis is a test.\n")

    out_dir = tmp_path / "Output"
    out_dir.mkdir()

    args = [str(md_file), "-o", str(out_dir), name_option, "myname"]
    marksplitz.main(args)

    assert (out_dir / "myname-001.html").exists()


@pytest.mark.parametrize("outdir_option", ["-o", "--output-dir"])
def test_output_dir_option(tmp_path, outdir_option):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\nThis is a test.\n")

    out_dir = tmp_path / "OutputPages"
    out_dir.mkdir()

    args = [str(md_file), outdir_option, str(out_dir)]
    marksplitz.main(args)

    assert (out_dir / "page-001.html").exists()


@pytest.mark.parametrize("images_option", ["-i", "--images-subdir"])
def test_copy_images_subdir(tmp_path, images_option):
    # Create a temporary directory with a Markdown file and an images subdirectory.
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n" "This is a test.\n" "![Image](images/image.png)\n")

    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "image.png").write_text("I am a bad PNG!")

    # Create a temporary directory for the output.
    out_dir = tmp_path / "Output"
    out_dir.mkdir()

    # Run the main function passing the Markdown file and output directory.
    args = [str(md_file), "-o", str(out_dir), images_option, "images"]
    marksplitz.main(args)

    # Check that the output directory contains the expected files.
    assert (out_dir / "page-001.html").exists()
    assert (out_dir / "images").exists()
    assert (out_dir / "images" / "image.png").exists()
