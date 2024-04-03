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
    assert (out_dir / "output-001.html").exists()
    assert (out_dir / "output-002.html").exists()
    assert (out_dir / "output-003.html").exists()

    # Check that the output files contains some of the expected content.
    text1 = (out_dir / "output-001.html").read_text()
    assert "<h1>Test</h1>" in text1
    assert "<p>This is a test.</p>" in text1

    text2 = (out_dir / "output-002.html").read_text()
    assert "<h2>Section 1</h2>" in text2
    assert "<p>This is section 1.</p>" in text2

    text3 = (out_dir / "output-003.html").read_text()
    assert "<h2>Section 2</h2>" in text3
    assert "<p>This is section 2.</p>" in text3
