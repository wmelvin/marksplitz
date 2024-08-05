from __future__ import annotations

import hashlib
from pathlib import Path
from textwrap import dedent

import pytest
from marksplitz import marksplitz


@pytest.fixture
def tmp_markdown_file_with_code(tmp_path) -> tuple[Path, str]:
    """Create a temporary Markdown file with code blocks.

    Returns:
        tuple[Path, str]: A tuple with the path to the Markdown file
        and the hash of the code block.
    """
    md_file = tmp_path / "test.md"

    code_block = 'print("Hello from Python.")'

    sha1 = hashlib.sha1(usedforsecurity=False)

    # When the code block is extracted from the Markdown file, it will have
    # a newline at the end, so include that in the hash.
    sha1.update(f"{code_block}\n".encode("utf-8"))
    code_hash = sha1.hexdigest()[:8]

    md_file.write_text(
        dedent(
            f"""\
            # Test

            ___

            ## Page 1

            This is a test.

            [GitHub](https://github.com/wmelvin)

            ---

            ## Page 2

            This page has a code block.

            ``` python
            {code_block}
            ```

            ---

            ## Page 3

            This page has a code block with a code-file directive.

            <!-- code-file: hello.py -->
            ``` python
            {code_block}
            ```

            """
        )
    )
    return md_file, code_hash


def test_markdown_file_with_code_no_subdir(tmp_markdown_file_with_code):
    md_file, _ = tmp_markdown_file_with_code

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

    cb = '<pre><code class="language-python">print(&quot;Hello from Python.&quot;)'

    # Code block should be in page-002.html in a <pre><code> element.
    assert cb in (out_dir / "page-002.html").read_text()

    # Code block should be in page-003.html in a <pre><code> element
    # because no --code-subdir was specified.
    assert cb in (out_dir / "page-003.html").read_text()


def test_markdown_file_with_code_and_subdir_arg(tmp_markdown_file_with_code):
    md_file, code_hash = tmp_markdown_file_with_code

    # Create temporary directories.
    out_dir = md_file.parent / "Output"
    out_dir.mkdir()

    code_dir = md_file.parent / "code_files"
    code_dir.mkdir()

    img_dir = md_file.parent / "images"
    img_dir.mkdir()

    # Run the main function passing the Markdown file and output directory.
    args = [
        str(md_file),
        "-o",
        str(out_dir),
        "--code-subdir",
        "code_files",
        "--images-subdir",
        "images",
    ]
    marksplitz.main(args)

    # Check that the output directory contains the expected files.
    assert (out_dir / "page-001.html").exists()
    assert (out_dir / "page-002.html").exists()
    assert (out_dir / "page-003.html").exists()

    # Code file should exist in the code_files directory.
    code_file = code_dir / f"hello.{code_hash}.py"
    assert code_file.exists()

    cb = '<pre><code class="language-python">print(&quot;Hello from Python.&quot;)'

    # Code block should be in page-002.html in a <pre><code> element.
    assert cb in (out_dir / "page-002.html").read_text()

    pg3 = (out_dir / "page-003.html").read_text()

    # Code block should not be in page-003.html in a <pre><code> element.
    assert cb not in pg3

    # Because no image exists for the code file, the code block should be
    # replaced with a message.
    assert "No code image for 'hello" in pg3


def test_markdown_file_with_code_subdir_and_image(tmp_markdown_file_with_code):
    md_file, code_hash = tmp_markdown_file_with_code

    # Create temporary directories.
    out_dir = md_file.parent / "Output"
    out_dir.mkdir()

    code_dir = md_file.parent / "code_files"
    code_dir.mkdir()

    img_dir = md_file.parent / "images"
    img_dir.mkdir()

    # Create a code image file.
    code_img = img_dir / f"codeimg_hello.{code_hash}.png"
    code_img.write_text("I'm not a real PNG :(")

    # Run the main function passing the Markdown file and output directory.
    args = [
        str(md_file),
        "-o",
        str(out_dir),
        "--code-subdir",
        "code_files",
        "--images-subdir",
        "images",
    ]
    marksplitz.main(args)

    # Check that the output directory contains the expected files.
    assert (out_dir / "page-001.html").exists()
    assert (out_dir / "page-002.html").exists()
    assert (out_dir / "page-003.html").exists()

    # Code file should exist in the code_files directory.
    code_file = code_dir / f"hello.{code_hash}.py"
    assert code_file.exists()

    cb = '<pre><code class="language-python">print(&quot;Hello from Python.&quot;)'

    # Code block should be in page-002.html in a <pre><code> element.
    assert cb in (out_dir / "page-002.html").read_text()

    pg3 = (out_dir / "page-003.html").read_text()

    # Code block should not be in page-003.html in a <pre><code> element.
    assert cb not in pg3

    # The code block should be replaced with an image tag.
    im = f'<img src="images/codeimg_hello.{code_hash}.png" alt="hello.py"'
    assert im in pg3
