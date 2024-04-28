"""Split a Markdown file into linked HTML pages."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent, indent
from typing import NamedTuple

import mistune

__version__ = "0.1.dev11"


run_dt = datetime.now()


class AppOptions(NamedTuple):
    md_path: Path
    out_path: Path
    output_name: str
    images_subdir: str
    css_path: Path


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
            width: 80%;
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


def script_keyboard_nav(prev_page: str, next_page: str) -> str:
    """Return a script to navigate using the left and right arrow keys.

    The arrow keys move to the previous or next page. If there is no
    previous or next page, the corresponding navigation is excluded.
    The script is returned as a string.
    """
    if prev_page:
        case_prev = dedent(
            f"""\
            case "ArrowLeft":
                window.location.href = "{prev_page}";
                break;
            case "PageUp":
                window.location.href = "{prev_page}";
                break;
            """
        )
    else:
        case_prev = ""

    if next_page:
        case_next = dedent(
            f"""\
            case "ArrowRight":
                window.location.href = "{next_page}";
                break;
            case "PageDown":
                window.location.href = "{next_page}";
                break;
            """
        )
    else:
        case_next = ""

    s = dedent(
        """\
        <script type="text/javascript">
            document.addEventListener('keydown', function(event) {
                const key = event.key;
                switch (key) {
        """
    )

    if case_prev:
        s += indent(case_prev, " " * 12)

    if case_next:
        s += indent(case_next, " " * 12)

    s += dedent(
        """\
                    default:
                        break;
                }
            });
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
    s += f"{script_keyboard_nav(prev_page, next_page)}\n"
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
                    a:link, a:visited { color: navy; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                  </style>
                  <link rel="stylesheet" type="text/css" href="custom.css">
                  <base target="_blank">
                </head>
                <body>
                <div id="container">
                <div id="content">
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

        f.write(
            dedent(
                """\
                </ol>
                </div>
                </div>
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
        images_subdir = md_path.parent / args.images_subdir
        if not images_subdir.exists():
            sys.stderr.write(f"\nDirectory not found: {images_subdir}\n")
            sys.exit(1)

    output_name = args.output_name if args.output_name else "page"

    css_path = out_path / args.css_file if args.css_file else None

    return AppOptions(
        md_path=md_path,
        out_path=out_path,
        output_name=output_name,
        images_subdir=args.images_subdir,
        css_path=css_path,
    )


def copy_images_subdir(opts: AppOptions) -> None:
    """Copy the source images subdirectory to the output directory.

    Existing files in the output directory are overwritten.
    If no images subdirectory is specified, nothing is done.
    """
    if opts.images_subdir:
        src_path = opts.md_path.parent / opts.images_subdir
        dst_path = opts.out_path / opts.images_subdir
        if not dst_path.exists():
            dst_path.mkdir()
        for src_file in src_path.iterdir():
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


def add_target_blank(html: str) -> str:
    """Add 'target="_blank"' to all external links in the HTML."""
    return html.replace('<a href="http', '<a target="_blank" href="http')


def main(arglist=None) -> int:
    """Split a Markdown file into linked HTML pages."""
    opts = get_options(arglist)

    print(f"\nReading '{opts.md_path}'")

    src_md = opts.md_path.read_text().splitlines(keepends=True)

    pages = []
    t = ""
    for line in src_md:
        s = line.strip()
        if s == "---":
            if t:
                pages.append(t)
                t = ""
        else:
            t += line

    if t:
        pages.append(t)

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

        for num, text in enumerate(pages, start=1):
            md, pg_title, heading_level = extract_title_comments(num, text)

            md, add_classes = extract_class_comments(md)

            filename, prev_page, next_page = output_filenames(
                opts.output_name, num, len(pages)
            )

            index_items.append((filename, pg_title, heading_level))

            html = html_head(
                f"{num}. {pg_title}", num, prev_page, css_link, add_classes
            )

            html += mistune.html(md)

            html = add_target_blank(html)

            html += html_tail(prev_page, next_page)

            html_file = opts.out_path / filename
            print(f"Writing '{html_file}'")
            html_file.write_text(html)

        copy_images_subdir(opts)

        write_index(opts.out_path, index_items)

    return 0


if __name__ == "__main__":
    main()
