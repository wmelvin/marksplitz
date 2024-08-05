"""Split a Markdown file into linked HTML pages."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import NamedTuple

import mistune

APP_NAME = "marksplitz"

__version__ = "0.1.dev20"


run_dt = datetime.now()

warnings = []


class AppOptions(NamedTuple):
    md_path: Path
    out_path: Path
    output_name: str
    images_subdir: str
    images_path: Path
    code_subdir: str
    code_path: Path
    css_path: Path
    img_delay: int = 0


def html_style() -> str:
    """Return a default style for the HTML output as a string."""
    return dedent(
        """\
        body { font-family: sans-serif; }

        h1 {
            color: #004578;
            text-align: center;
        }

        h2 {
            color: #002452;
            margin-top: 2rem;
        }

        h3 { color: #001541; }

        img {
            border: 1px solid #dde;
            border-radius: 6px;
            height: auto;
            max-width: 80%;
        }

        li { margin-top: 0.8rem; }

        blockquote {
            border: 1px solid #b0e0e6;
            border-radius: 6px;
            color: darkslategray;
            padding: 0px 4px;
        }

        code {
            background-color: #eee;
            padding-left: 0.3rem;
            padding-right: 0.3rem;
            font-family: monospace;
        }

        #container {
            margin: 0.3rem;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 600px;
        }

        #content {
            border: 1px solid silver;
            padding: 2rem 10%;
            width: 900px;
            max-width: 90%;
        }

        .text-center { text-align: center; }

        .nav-link {
            padding-top: 2rem;
            width: 3rem;
        }

        .nav-link a {
            border: 1px solid silver;
            border-radius: 5px;
            font-size: 20px;
            font-weight: bold;
            margin: 0.5rem;
            padding: 0.5rem;
        }

        #nav-prev, #nav-next { visibility: hidden; }

        #container.show-nav #nav-prev { visibility: visible; }

        #container.show-nav #nav-next { visibility: visible; }

        a:link, a:visited {
            color: navy;
            text-decoration: none;
        }

        a:hover { text-decoration: underline; }
        """
    )


def nav_link_div(div_id: str, target: str, anchor: str) -> str:
    """Return a div containing a navigation link as a string.

    If no target is provided, the anchor tag is not included.
    """
    s = f'<div id="{div_id}" class="nav-link">\n'
    if target:
        s += f'  <a href="{target}">{anchor}</a>\n'
    s += "</div>\n"
    return s


def html_head(
    title: str,
    page_num: int,
    prev_page: str,
    css_link: str,
    add_classes: str,
) -> str:
    """Return the head section of an HTML file as a string.

    The title is used as the page title. The page number is used to add a
    class to the 'container' div. If a CSS link is provided, it is
    included in the head section. If no CSS link is provided, a default style
    is embedded in the HTML output. If additional classes are provided, they
    are added to the 'content' div. If an 'add_id' is provided, it is added
    to the 'content' div.

    param title: The title of the page.
    param page_num: The page number.
    param prev_page: The filename of the previous page.
    param css_link: A link to a CSS file.
    param add_classes: Additional classes to add to the content div.
    """
    s = dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <title>{title}</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        """
    )

    if css_link:
        s += f"{css_link}\n"
    else:
        s += f"<style>\n{html_style()}</style>\n"

    s += '<link rel="stylesheet" type="text/css" href="custom.css">\n'

    s += f'</head>\n<body>\n<div id="container" class="page-{page_num:03}">\n\n'

    s += nav_link_div("nav-prev", prev_page, "&larr;")

    class_str = f' class="{add_classes}"' if add_classes else ""

    s += f'\n<div id="content"{class_str}>\n'

    return s


def script_nav_keyboard_or_swipe(prev_page: str, next_page: str) -> str:
    """Return a script to navigate between pages.

    The script provides two methods for navigating to the next or previous page.

    The first method listens for a 'keydown' event to navigate using
    the left and right arrow keys and the Page Up and Page Down keys.

    The second method adds event listeners for touchstart and touchend
    events to navigate using swipe gestures. The difference in X and Y
    coordinates is used to determine the direction of the swipe.

    The previous and next page filenames are used to create navigation links.

    The script is returned as a string.
    """
    s = dedent(
        f"""\
        <script type="text/javascript">
            let startX = 0;
            let startY = 0;
            let endX = 0;
            let endY = 0;
            let prevPage = '{prev_page}';
            let nextPage = '{next_page}';
            const MIN_SWIPE = 30;

        """
    )
    s += dedent(
        """\
            document.addEventListener('keydown', function(event) {
                const key = event.key;
                switch (key) {
                    case "ArrowLeft":
                        if (prevPage) { window.location.href = prevPage; }
                        break;
                    case "PageUp":
                        if (prevPage) { window.location.href = prevPage; }
                        break;
                    case "ArrowRight":
                        if (nextPage) { window.location.href = nextPage; }
                        break;
                    case "PageDown":
                        if (nextPage) { window.location.href = nextPage; }
                        break;
                    default:
                        break;
                }
            });

            document.addEventListener('touchstart', (event) => {
                startX = event.changedTouches[0].screenX;
                startY = event.changedTouches[0].screenY;
            }, false);

            document.addEventListener('touchend', (event) => {
                endX = event.changedTouches[0].screenX;
                endY = event.changedTouches[0].screenY;
                handleSwipe();
            }, false);

            function handleSwipe() {
                let diffX = endX - startX;
                let diffY = endY - startY;

                if (Math.abs(diffX) > Math.abs(diffY)) {
                    if (Math.abs(diffX) > MIN_SWIPE) {
                        if (diffX > 0) {  // Swipe right
                            if (prevPage) { window.location.href = prevPage; }
                        } else {  // Swipe left
                            if (nextPage) { window.location.href = nextPage; }
                        }
                    }
                } else {
                    if (Math.abs(diffY) > MIN_SWIPE) {
                        if (diffY > 0) {  // Swipe down
                            if (prevPage) { window.location.href = prevPage; }
                        } else {  // Swipe up
                            if (nextPage) { window.location.href = nextPage; }
                        }
                    }
                }
            }
        </script>
        """
    )
    return s


def script_nav_show_hide() -> str:
    """Return a script to show and hide navigation elements.

    The script adds a class to the 'container' div when the mouse is moved
    and removes the class after a delay. The class is used to show or hide
    the navigation elements.

    If a previous timeout exists, it is cleared before setting a new one.
    Timeout is in milliseconds.
    """
    return dedent(
        """\
        <script type="text/javascript">
            var containerDiv = document.getElementById('container');
            var timeoutId;
            document.addEventListener('mousemove', function() {
                containerDiv.classList.add('show-nav');
                if (timeoutId) {
                    clearTimeout(timeoutId);
                }
                timeoutId = setTimeout(function() {
                    containerDiv.classList.remove('show-nav');
                }, 2000);
            });
        </script>
        """
    )


def html_tail(prev_page: str, next_page: str) -> str:
    """Return the tail section of an HTML file as a string.

    The 'content' and 'container' divs are closed.
    The previous and next page filenames are used to create navigation
    links. The script to navigate using the keyboard is included.
    The script to show and hide navigation elements is also included.
    The body and html tags are closed.
    """
    s = "</div>  <!-- content -->\n\n"
    s += nav_link_div("nav-next", next_page, "&rarr;")
    s += "\n</div>  <!-- container -->\n\n"
    s += f"{script_nav_keyboard_or_swipe(prev_page, next_page)}\n"
    s += f"{script_nav_show_hide()}\n"
    s += "</body>\n</html>\n"
    return s


def write_index(out_path: Path, items: list[tuple[str, str]]) -> None:
    """Write an index file with links to the pages.

    The file is named 'index.html' and is written to the output directory.
    The parameter 'items' is a list of tuples containing the filename,
    title, and heading level of each page.
    """
    index_file = out_path / "index.html"
    print(f"Writing '{index_file}'")
    with index_file.open("w") as f:
        f.write(
            dedent(
                """\
                <!DOCTYPE html>
                <html lang='en'>
                <head>
                  <title>Index</title>
                  <style>
                    body { font-family: sans-serif; }
                    li {
                        border: 1px solid #dde;
                        border-radius: 5px;
                        margin: 0.3rem;
                        padding: 0.3rem;
                    }
                    #container { display: flex; justify-content: center; }
                    #content { max-width: 900px; }
                    #foot {
                        border-top: 1px solid gray;
                        font-family: monospace;
                        font-size: small;
                        margin-top: 3rem;
                        padding-top: 1rem;
                    }
                    a:link, a:visited { color: navy; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                  </style>
                  <link rel="stylesheet" type="text/css" href="custom.css">
                  <base target="_blank">
                </head>
                <body>
                <div id="container">
                <div id="content">
                <p>
                Navigate pages using Left and Right arrow, Page Up, and Page Down.</p>
                <p>See also:
                <a href="links.html">Extracted links</a>,
                <a href="one-page.html">One-page version</a>
                </p>
                <h1>Index of Pages</h1>
                <ol>
                """
            )
        )

        for filename, title, level in items:
            f.write(
                f'  <li class="index-lev-{level}"><a href="{filename}">{title}</a>'
                "</li>\n"
            )

        foot_div = (
            f'<div id="foot">\nCreated by {APP_NAME} '
            f"v{__version__} at {run_dt.strftime('%Y-%m-%d %H:%M')}\n"
            "</div>\n"
        )
        f.write(
            dedent(
                f"""\
                </ol>
                {foot_div}
                </div>
                </div>
                </body>
                </html>
                """
            )
        )


def write_one_page(out_path: Path, html_all: list[str]) -> None:
    html_file = out_path / "one-page.html"
    print(f"Writing '{html_file}'")
    with html_file.open("w") as f:
        f.write(
            dedent(
                """\
                <!DOCTYPE html>
                <html lang='en'>
                <head>
                  <title>One-Page</title>
                  <style>
                    body {
                        font-family: sans-serif;
                        margin: 4rem;
                    }
                    #foot {
                        border-top: 1px solid gray;
                        font-family: monospace;
                        font-size: small;
                        margin-top: 3rem;
                        padding-top: 1rem;
                    }
                  </style>
                </head>
                <body>
                """
            )
        )

        for page in html_all:
            for line in page.splitlines():
                f.write(f"{line}\n")
            f.write("\n<p>&nbsp;</p>\n<hr>\n<p>&nbsp;</p>\n")

        foot_msg = (
            f"Created by {APP_NAME} v{__version__} at "
            f"{run_dt.strftime('%Y-%m-%d %H:%M')}"
        )
        f.write(
            dedent(
                f"""\
                <div id="foot">{foot_msg}</div>
                </body>
                </html>
                """
            )
        )


def write_links_page(out_path: Path, html_all: list[str]) -> None:
    html_file = out_path / "links.html"
    print(f"Writing '{html_file}'")
    with html_file.open("w") as f:
        f.write(
            dedent(
                """\
                <!DOCTYPE html>
                <html lang='en'>
                <head>
                  <title>Extracted Links</title>
                  <style>
                    body {
                        font-family: sans-serif;
                        margin: 4rem;
                    }
                    #foot {
                        border-top: 1px solid gray;
                        font-family: monospace;
                        font-size: small;
                        margin-top: 3rem;
                        padding-top: 1rem;
                    }
                  </style>
                </head>
                <body>
                """
            )
        )

        for page in html_all:
            found_heading = False
            is_h1 = False
            found_link = False
            pg = ""
            for line in page.splitlines():
                s = line.strip()

                if not found_heading and s.lower().startswith(
                    ("<h1>", "<h2>", "<h3>", "<h4>")
                ):
                    found_heading = True
                    if s.lower().startswith("<h1>"):
                        is_h1 = True
                    pg += f"{line}\n"

                if "<a " in s.lower():
                    found_link = True
                    pg += f"{line}\n"

            if found_link or is_h1:
                f.write(f"{pg}\n<p>&nbsp;</p>\n<hr>\n<p>&nbsp;</p>\n")

        foot_msg = (
            f"Created by {APP_NAME} v{__version__} at "
            f"{run_dt.strftime('%Y-%m-%d %H:%M')}"
        )
        f.write(
            dedent(
                f"""\
                <div id="foot">{foot_msg}</div>
                </body>
                </html>
                """
            )
        )


def output_filenames(
    base_filename: str, num: int, n_pages: int
) -> tuple[str, str, str]:
    """Return the filenames of the current, previous, and next pages.

    If there is no previous or next page, the  corresponding filename
    is an empty string. The filenames are returned as a tuple of strings.
    """
    prev_filename = "" if num == 1 else f"{base_filename}-{num - 1:03}.html"
    next_filename = "" if num == n_pages else f"{base_filename}-{num + 1:03}.html"
    filename = f"{base_filename}-{num:03}.html"
    return filename, prev_filename, next_filename


def get_args(arglist=None):
    """Get the command-line arguments and return the parsed arguments."""
    ap = argparse.ArgumentParser(
        description="Split a Markdown file into linked HTML pages."
    )

    ap.add_argument(
        "markdown_file",
        help="Path to the Markdown file to split.",
    )

    ap.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        help="Path to the output directory.",
    )

    ap.add_argument(
        "-n",
        "--output-name",
        dest="output_name",
        help="Base name for the output HTML files.",
    )

    ap.add_argument(
        "-i",
        "--images-subdir",
        dest="images_subdir",
        help="Subdirectory for images. Expected to be in the directory containing "
        "the Markdown file. Contents are copied to a subdirectory by the same "
        "name in the output directory.",
    )

    ap.add_argument(
        "-d",
        "--code-subdir",
        dest="code_subdir",
        help="Subdirectory for code files. Expected to be in the directory containing "
        "the Markdown file. Fenced code blocks, marked with a code-file directive, "
        "are written to this directory.",
    )

    ap.add_argument(
        "--img-delay",
        dest="img_delay",
        type=int,
        default=0,
        help="Delay in seconds to wait for a code-file image to be created.",
    )

    ap.add_argument(
        "-c",
        "--css-file",
        dest="css_file",
        help="Optional name of a CSS file to include in the same location as the HTML "
        "output. If a CSS file is not specified, a default style is embedded in the "
        "HTML output. If a CSS file is specified, the default style is not included."
        "If the specified CSS file does not exist, it is created with the default "
        "style.",
    )

    return ap.parse_args(arglist)


def get_options(arglist=None) -> AppOptions:
    """Get the command-line arguments and return an AppOptions object."""
    args = get_args(arglist)

    md_path = Path(args.markdown_file)
    if not md_path.exists():
        sys.stderr.write(f"\nFile not found: {md_path}\n")
        sys.exit(1)

    if args.output_dir:
        out_path = Path(args.output_dir)
        # If an output directory is specified, it must exist.
        if not out_path.exists():
            sys.stderr.write(f"\nDirectory not found: {out_path}\n")
            sys.exit(1)
    else:
        dir_name = md_path.parent / f"Pages_{run_dt:%Y%m%d_%H%M%S}"
        out_path = md_path.parent / dir_name
        # Default directory should not already exist.
        if out_path.exists():
            sys.stderr.write(f"\nDirectory already exists: {out_path}\n")
            sys.exit(1)
        out_path.mkdir()

    if args.images_subdir:
        images_path = md_path.parent / args.images_subdir
        if not images_path.exists():
            print(f"Creating images subdirectory: {images_path}")
            images_path.mkdir()
    else:
        images_path = None

    if args.code_subdir:
        code_path = md_path.parent / args.code_subdir
        if not code_path.exists():
            print(f"Creating code subdirectory: {code_path}")
            code_path.mkdir()
    else:
        code_path = None

    output_name = args.output_name if args.output_name else "page"

    css_path = out_path / args.css_file if args.css_file else None

    return AppOptions(
        md_path=md_path,
        out_path=out_path,
        output_name=output_name,
        images_subdir=args.images_subdir,
        images_path=images_path,
        code_subdir=args.code_subdir,
        code_path=code_path,
        css_path=css_path,
        img_delay=args.img_delay,
    )


def copy_images_subdir(opts: AppOptions) -> None:
    """Copy the source images subdirectory to the output directory.

    Existing files in the output directory are overwritten.
    If no images subdirectory is specified, nothing is done.
    """
    if opts.images_subdir:
        dst_path = opts.out_path / opts.images_subdir
        if not dst_path.exists():
            dst_path.mkdir()
        for src_file in opts.images_path.iterdir():
            if not src_file.is_file():
                continue
            dst_file = dst_path / src_file.name
            print(f"Copy '{src_file}'\n  to '{dst_file}'")
            shutil.copy2(src_file, dst_file)


def get_page_heading(num: int, text: str) -> tuple[str, int]:
    """Return the first heading in the text and its heading-level.

    If there is no heading, return a default heading level and title.
    """
    heading_level = 1
    lines = text.splitlines()
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            a = s.split(" ", 1)
            heading_level = a[0].count("#")
            return (a[1].strip(), heading_level)
    return (f"Page {num}", heading_level)


def extract_title_comments(num: int, text: str) -> tuple[str, str, int]:
    """Extract the title from a comment in the text.

    Returns a tuple of the text, with title-comments removed, and the title
    extracted from the comments.

    There should only be one title comment in the text. If there is more than
    one, the last one is used.

    If there is no title comment, the first Markdown heading in the text is used
    as the title.

    The headling level is based on the first Markdown heading in the text.

    Returns a tuple of the text, the title, and the heading level.
    """
    title = ""

    # TODO: Should a title-comment also be able to set heading-level?
    # If so, leading '#' characters could be used same as in Markdown.

    # Look for, and remove, a title comment.
    out_lines = []
    lines = text.splitlines(keepends=True)
    for line in lines:
        s = line.strip()
        if s.startswith("<!-- title: "):
            title = s[12:-3].strip()
        else:
            out_lines.append(line)

    heading, heading_level = get_page_heading(num, text)

    # If there was no title comment, use the first heading as the title.
    if not title:
        title = heading

    return "".join(out_lines), title, heading_level


def extract_class_comments(text: str) -> tuple[str, str]:
    """Extract classes from comments in the text.

    Returns a tuple of the text, with class-comments removed, and the
    classes extracted from the comments. If there are multiple classes
    in the comments, they are concatenated with spaces.

    The text and classes are returned as strings.
    """
    classes = ""
    out_lines = []
    lines = text.splitlines(keepends=True)
    for line in lines:
        s = line.strip()
        if s.startswith("<!-- class: "):
            classes = s[12:-3].strip()
        else:
            out_lines.append(line)

    return "".join(out_lines), classes


def delete_obsolete_image_file(old_code_file: Path, opts: AppOptions) -> None:
    img_path = opts.images_path / f"codeimg_{old_code_file.with_suffix('.png').name}"
    if img_path.exists():
        print(f"Delete obsolete '{img_path.name}'")
        img_path.unlink()


def delete_obsolete_code_file(code_file: Path, opts: AppOptions) -> None:
    # Get the first part of the file name up to the hash.
    s = code_file.name.rsplit(".", 2)[0]

    # Delete any of the same code-file with a different hash.
    files = list(code_file.parent.glob(f"{s}*"))
    for file in files:
        if file.name == code_file.name:
            continue
        print(f"Delete obsolete '{file.name}'")
        file.unlink()
        delete_obsolete_image_file(file, opts)


def extract_code_files(text: str, opts: AppOptions) -> str:
    """Extract code blocks from the text and write them to files
    based on the file names specified in a HTML comment preceeding
    the fenced code block.

    Returns the text with code-file comments removed.

    The text is returned as a string.
    """
    if not ("<!-- code-file:" in text and opts.images_path and opts.code_path):
        return text

    out_lines = []
    code_filename = ""
    code_text = ""
    in_code_block = False
    lines = text.splitlines(keepends=True)
    for line in lines:
        s = line.strip()

        if s.startswith("<!-- code-file:"):
            code_filename = s[15:-3].strip()
        elif s.startswith("```"):
            if in_code_block and code_text and code_filename:
                # Add a hash of the code to the filename so corresponding
                # code-image file is invalidated if the code changes.
                sha1 = hashlib.sha1(usedforsecurity=False)
                sha1.update(code_text.encode("utf-8"))
                # The first 8 characters should be enough for this purpose.
                text_hash = sha1.hexdigest()[:8]

                code_file = Path(code_filename)
                code_file = (
                    opts.code_path / f"{code_file.stem}.{text_hash}{code_file.suffix}"
                )

                delete_obsolete_code_file(code_file, opts)

                # Because the file name includes a hash of the text,
                # the file is only written if the code has changed.
                if code_file.exists():
                    print(f"Not changed: '{code_file}'")
                else:
                    print(f"Writing code '{code_file}'")
                    code_file.write_text(code_text)

                code_image = opts.images_path / f"codeimg_{code_file.stem}.png"

                if opts.img_delay and not code_image.exists():
                    print(f"Waiting {opts.img_delay} seconds for '{code_image.name}'")
                    time.sleep(opts.img_delay)

                if code_image.exists():
                    img = Path(opts.images_subdir) / code_image.name
                    out_lines.append(f"\n![{code_filename}]({img})\n")
                else:
                    warnings.append(f"WARNING: No code image for '{code_file.name}'")
                    out_lines.append(
                        '\n<p style="color: red;">'
                        f"No code image for '{code_file.name}'"
                        "</p>\n"
                    )

                code_filename = ""
                code_text = ""
            in_code_block = not in_code_block
        elif in_code_block:
            code_text += line
        else:
            out_lines.append(line)

    return "".join(out_lines)


def add_target_blank(html: str) -> str:
    """Add 'target="_blank"' to all external links in the HTML."""
    return html.replace('<a href="http', '<a target="_blank" href="http')


def show_warnings():
    if warnings:
        print("")
        for w in warnings:
            print(w)
    print("")


def main(arglist=None) -> int:
    """Split a Markdown file into linked HTML pages."""
    opts = get_options(arglist)

    print(f"\nReading '{opts.md_path}'")

    src_md = opts.md_path.read_text().splitlines(keepends=True)

    pages = []
    page_text = ""
    for line in src_md:
        s = line.strip()
        if s == "---":
            if page_text:
                if "<!-- no-pub -->" not in page_text:
                    pages.append(page_text)
                page_text = ""
        else:
            page_text += line

    if page_text and ("<!-- no-pub -->" not in page_text):
        pages.append(page_text)

    if pages:
        if opts.css_path:
            if not opts.css_path.exists():
                print(f"Writing '{opts.css_path}'")
                opts.css_path.write_text(html_style())
            css_link = (
                f'<link rel="stylesheet" type="text/css" href="{opts.css_path.name}">'
            )
        else:
            css_link = ""

        index_items = []

        html_all = []

        for num, text in enumerate(pages, start=1):
            md, pg_title, heading_level = extract_title_comments(num, text)

            md, add_classes = extract_class_comments(md)

            md = extract_code_files(md, opts)

            filename, prev_page, next_page = output_filenames(
                opts.output_name, num, len(pages)
            )

            index_items.append((filename, pg_title, heading_level))

            html = html_head(
                f"{num}. {pg_title}", num, prev_page, css_link, add_classes
            )

            md_html = mistune.html(md)
            md_html = add_target_blank(md_html)
            html += md_html
            html_all.append(md_html)

            html += html_tail(prev_page, next_page)

            html_file = opts.out_path / filename
            print(f"Writing '{html_file}'")
            html_file.write_text(html)

        copy_images_subdir(opts)

        write_index(opts.out_path, index_items)
        write_one_page(opts.out_path, html_all)
        write_links_page(opts.out_path, html_all)
        show_warnings()

    return 0


if __name__ == "__main__":
    main()
