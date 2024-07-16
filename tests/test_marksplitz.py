from pathlib import Path
from textwrap import dedent

import mistune
import pytest
from marksplitz import marksplitz


@pytest.fixture
def tmp_markdown_file(tmp_path) -> Path:
    md_file = tmp_path / "test.md"
    md_file.write_text(
        dedent(
            """
            # Test

            ___

            ## Page 1

            This is a test.

            [GitHub](https://github.com/wmelvin)

            ---

            ## Page 2

            This is section 2.

            A bulleted list:

            - Item A
            - Item B
            - Item C

            > A block quote

            A numbered list:

            1. Item 1
            2. Item 2
            3. Item 3

            ---

            ## Page X

            This page should be excluded from the output.

            <!-- no-pub -->

            ---

            ## Page 3

            This is section 3.

            Some inline `code`.

            A block of code:

            ``` python
            from pathlib import Path

            print(Path.cwd())
            ```

            <h4>HTML Element (h4)</h4>

            Sup: <sup>superscript</sup>

            Sub: <sub>subscript</sub>
            """
        )
    )
    return md_file


def test_split_markdown_file(tmp_markdown_file):
    md_file = tmp_markdown_file

    # Create a temporary directory for the output.
    out_dir = md_file.parent / "Output"
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

    # assert '<a href="https://github.com/wmelvin">GitHub</a>' in text1
    assert '<a target="_blank" href="https://github.com/wmelvin">GitHub</a>' in text1

    text2 = (out_dir / "page-002.html").read_text()
    assert "<h2>Page 2</h2>" in text2
    assert "<p>This is section 2.</p>" in text2

    text3 = (out_dir / "page-003.html").read_text()
    assert "<h2>Page 3</h2>" in text3
    assert "<p>This is section 3.</p>" in text3

    # Write text files to manually compare rendering options
    # in tmp location.
    md = md_file.read_text()
    (md_file.parent / "mistune.html.txt").write_text(mistune.html(md))
    (md_file.parent / "mistune.markdown.txt").write_text(mistune.markdown(md))


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


def test_copy_images_with_existing_file(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n" "This is a test.\n" "![Image](images/image.png)\n")

    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "image.png").write_text("I am a bad PNG!")

    out_dir = tmp_path / "Output"
    out_dir.mkdir()

    args = [str(md_file), "-o", str(out_dir), "-i", "images"]
    marksplitz.main(args)

    assert (out_dir / "images" / "image.png").exists()

    # Should succeed when output directory and image file already exist.
    result = marksplitz.main(args)
    assert result == 0


@pytest.mark.parametrize("css_option", ["-c", "--css-file"])
def test_css_file_option(tmp_path, css_option):
    # Create a temporary directory with a Markdown file and a CSS file.
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n" "This is a test.\n")

    # Create a temporary directory for the output.
    out_dir = tmp_path / "Output"
    out_dir.mkdir()

    args = [str(md_file), "-o", str(out_dir), css_option, "style.css"]
    marksplitz.main(args)

    html_file = out_dir / "page-001.html"
    assert html_file.exists()

    html_text = html_file.read_text()

    # Check that the HTML file does not contain the <style> tag.
    assert "<style>" not in html_text

    # Check that the HTML file contains the <link> tag.
    assert '<link rel="stylesheet" type="text/css" href="style.css">' in html_text

    # A CSS file containing default style should be created.
    css_file = out_dir / "style.css"
    assert css_file.exists()

    # Modify the CSS file to add a new style.
    with css_file.open("a") as f:
        f.write("\n.noclass { color: red; }\n")

    # Run the main function again to check that the CSS file is not overwritten.
    marksplitz.main(args)

    # Check that the CSS file contains the added style.
    text = css_file.read_text()
    assert ".noclass { color: red; }" in text


def test_class_comments(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text(
        dedent(
            """
            # Test

            ## Page 1

            This is a test.

            ---

            ## Page 2

            A bulleted list:

            - Item A
            - Item B
            - Item C

            <!-- class: class-1 -->

            ---

            <!-- class: class-1 class-2 -->

            ## Page 3

            A numbered list:

            1. Item 1
            2. Item 2
            3. Item 3

            """
        )
    )

    out_dir = tmp_path / "Output"
    out_dir.mkdir()

    args = [str(md_file), "-o", str(out_dir)]
    marksplitz.main(args)

    # assert (out_dir / "page-001.html").exists()
    assert (out_dir / "page-002.html").exists()
    assert (out_dir / "page-003.html").exists()

    # text1 = (out_dir / "page-001.html").read_text()

    text2 = (out_dir / "page-002.html").read_text()
    assert 'id="content" class="class-1"' in text2
    assert "<!-- class:" not in text2

    text3 = (out_dir / "page-003.html").read_text()
    assert 'id="content" class="class-1 class-2"' in text3
    assert "<!-- class:" not in text3


def test_creates_index_html(tmp_markdown_file):
    md_file = tmp_markdown_file

    out_dir = md_file.parent / "Output"
    out_dir.mkdir()

    args = [str(md_file), "-o", str(out_dir)]
    marksplitz.main(args)

    index_file = out_dir / "index.html"
    assert index_file.exists()

    index_text = index_file.read_text()
    assert '<a href="page-001.html">Test</a>' in index_text
    assert '<a href="page-002.html">Page 2</a>' in index_text
    assert '<a href="page-003.html">Page 3</a>' in index_text


def test_title_comments(tmp_markdown_file):
    md_file = tmp_markdown_file

    md_file.write_text(md_file.read_text() + "\n<!-- title: This Title -->\n")

    out_dir = md_file.parent / "Output"
    out_dir.mkdir()

    args = [str(md_file), "-o", str(out_dir)]
    marksplitz.main(args)

    index_file = out_dir / "index.html"
    assert index_file.exists()

    index_text = index_file.read_text()
    assert '<a href="page-001.html">Test</a>' in index_text
    assert '<a href="page-002.html">Page 2</a>' in index_text
    assert '<a href="page-003.html">This Title</a>' in index_text


def test_index_item_levels(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text(
        dedent(
            """
            # Test

            ## Section 1

            Section 1 content.

            ---

            ## Section 2

            Section 2 content.

            ---

            ### Section 2.1

            Section 2.1 content.

            ---

            #### Section 2.1.1

            Section 2.1.1 content.

            ---

            ### Section 2.2

            Section 2.2 content.

            ---

            ## Section 3

            Section 3 content.

            """
        )
    )

    out_dir = md_file.parent / "Output"
    out_dir.mkdir()

    args = [str(md_file), "-o", str(out_dir)]
    marksplitz.main(args)

    index_file = out_dir / "index.html"
    assert index_file.exists()

    index_text = index_file.read_text()
    assert '<link rel="stylesheet" type="text/css" href="custom.css">' in index_text
    assert '<li class="index-lev-1"><a href="page-001.html">Test</a>' in index_text
    assert '<li class="index-lev-2"><a href="page-002.html">Section 2</a>' in index_text
    assert (
        '<li class="index-lev-3"><a href="page-003.html">Section 2.1</a>' in index_text
    )
    assert (
        '<li class="index-lev-4"><a href="page-004.html">Section 2.1.1</a>'
        in index_text
    )
    assert (
        '<li class="index-lev-3"><a href="page-005.html">Section 2.2</a>' in index_text
    )
    assert '<li class="index-lev-2"><a href="page-006.html">Section 3</a>' in index_text
