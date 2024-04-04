from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent, indent
from typing import NamedTuple

import mistune

__version__ = "0.1.dev2"


run_dt = datetime.now()


class AppOptions(NamedTuple):
    md_path: Path
    out_path: Path
    output_name: str
    images_subdir: str
    css_path: Path


def html_style() -> str:
    return dedent(
        """\
        body { font-family: sans-serif; }
        h1 { color: gray; text-align: center; }
        img {
            border: 1px solid #dde;
            border-radius: 6px;
            height: auto;
            width: 90%;
        }
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
        .container {
            margin: 0.3rem;
            display: flex;
            /* align-items: center; */
            justify-content: center;
        }
        .content {
            border: 1px solid silver;
            padding: 2rem;
            width: 800px;
        }
        .text-center {
            text-align: center;
        }
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
        a:link, a:visited {
            color: brown;
            text-decoration: none;
        }
        """
    )


def nav_link_div(div_id: str, target: str, anchor: str):
    s = f'<div id="{div_id}" class="nav-link">\n'
    if target:
        s += f'  <a href="{target}">{anchor}</a>\n'
    s += "</div>\n"
    return s


def html_head(title: str, prevPage: str, css_link: str, add_classes: str) -> str:
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
    s += '</head>\n<body>\n<div class="container">\n\n'
    s += nav_link_div("nav-prev", prevPage, "&larr;")
    if add_classes:
        s += f'<div class="content {add_classes}">\n'
    else:
        s += '\n<div class="content">\n'
    return s


def script_keyboard_nav(prevPage: str, nextPage: str) -> str:
    """Return a script to navigate to the previous or next page using the
    left and right arrow keys. If there is no previous or next page, the
    corresponding navigation is excluded. The script is returned as a string.
    """
    if prevPage:
        case_prev = dedent(
            f"""\
            case "ArrowLeft":
                window.location.href = "{prevPage}";
                break;
            """
        )
    else:
        case_prev = ""

    if nextPage:
        case_next = dedent(
            f"""\
            case "ArrowRight":
                window.location.href = "{nextPage}";
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
    """Return a script to show the navigation buttons when the mouse is moved
    and hide them after a delay. The script is returned as a string.
    If a previous timeout exists, it is cleared before setting a new one.
    Timeout value is in milliseconds.
    """
    return dedent(
        """\
        <script type="text/javascript">
            var navPrev = document.getElementById('nav-prev');
            var navNext = document.getElementById('nav-next');
            var timeoutId;
            document.addEventListener('mousemove', function() {
                navPrev.style.visibility = 'visible';
                navNext.style.visibility = 'visible';
                if (timeoutId) {
                    clearTimeout(timeoutId);
                }
                timeoutId = setTimeout(function() {
                    navPrev.style.visibility = 'hidden';
                    navNext.style.visibility = 'hidden';
                }, 2000);
            });
        </script>
        """
    )


def html_tail(prevPage: str, nextPage: str) -> str:
    s = "</div>  <!-- content -->\n\n"
    s += nav_link_div("nav-next", nextPage, "&rarr;")
    s += "\n</div>  <!-- container -->\n\n"
    s += f"{script_keyboard_nav(prevPage, nextPage)}\n"
    s += f"{script_nav_show_hide()}\n"
    s += "</body>\n</html>\n"
    return s


def output_filenames(
    base_filename: str, num: int, n_pages: int
) -> tuple[str, str, str]:
    """Return the filename of the current page and the filenames of the
    previous and next pages. If there is no previous or next page, the
    corresponding filename is an empty string. The filenames are returned as a
    tuple of strings.
    """
    prev_filename = "" if num == 1 else f"{base_filename}-{num - 1:03}.html"
    next_filename = "" if num == n_pages else f"{base_filename}-{num + 1:03}.html"
    filename = f"{base_filename}-{num:03}.html"
    return filename, prev_filename, next_filename


def get_args(arglist=None):
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


def copy_images_subdir(opts: AppOptions):
    """Copy the source images subdirectory, if one is specified,
    to the output directory. Existing files in the output
    directory are overwritten.
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


def extract_class_comments(text) -> tuple[str, str]:
    """Return a tuple of the text with class comments removed and the
    classes extracted from the comments. The text is returned as a string.
    The classes are returned as a string.
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


def main(arglist=None) -> int:
    opts = get_options(arglist)

    print(f"\nReading '{opts.md_path}'")
    md = opts.md_path.read_text().splitlines(keepends=True)

    pages = []
    t = ""
    for line in md:
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

        for num, text in enumerate(pages, start=1):
            md, add_classes = extract_class_comments(text)

            filename, prevPage, nextPage = output_filenames(
                opts.output_name, num, len(pages)
            )

            html = html_head(f"Page {num}", prevPage, css_link, add_classes)

            html += mistune.html(md)

            html += html_tail(prevPage, nextPage)

            html_file = opts.out_path / filename
            print(f"Writing '{html_file}'")
            html_file.write_text(html)

        copy_images_subdir(opts)

    return 0


if __name__ == "__main__":
    main()
