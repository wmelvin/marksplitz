# marksplitz

Command-line utility to split a Markdown file into linked static web pages.

> Development work in progress.

## Directive Comments

The following HTML comments can be placed in the source Markdown document to alter the generated HTML.

`<!-- title: new-title -->` 

- Replace the default HTML **title** for the page.

`<!-- class: class-1 class-2 -->` 

- Add one or more classes to the `content` div.
- Use to apply additional styles via a `custom.css` file. 

`<!-- no-pub -->`

- Do not publish the page - exclude it from the HTML output.

## Command-line Usage

```
usage: marksplitz [-h] [-o OUTPUT_DIR] [-n OUTPUT_NAME] [-i IMAGES_SUBDIR]
                     [-c CSS_FILE]
                     markdown_file

Split a Markdown file into linked HTML pages.

positional arguments:
  markdown_file         Path to the Markdown file to split.

options:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Path to the output directory.
  -n OUTPUT_NAME, --output-name OUTPUT_NAME
                        Base name for the output HTML files.
  -i IMAGES_SUBDIR, --images-subdir IMAGES_SUBDIR
                        Subdirectory for images. Expected to be in the
                        directory containing the Markdown file. Contents are
                        copied to a subdirectory by the same name in the
                        output directory.
  -c CSS_FILE, --css-file CSS_FILE
                        Optional name of a CSS file to include in the same
                        location as the HTML output. If a CSS file is not
                        specified, a default style is embedded in the HTML
                        output. If a CSS file is specified, the default style
                        is not included.If the specified CSS file does not
                        exist, it is created with the default style.
```

## Reference

### CSS

Customizing the generated HTML output requires using CSS.

- MDN Guide: [Learn to style HTML using CSS](https://developer.mozilMDNla.org/en-US/docs/Learn/CSS)
- MDN Reference: [CSS: Cascading Style Sheets](https://developer.mozilla.org/en-US/docs/Web/CSS)
  - [Basic concepts of flexbox](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_flexible_box_layout/Basic_concepts_of_flexbox)
  - [Class selectors](https://developer.mozilla.org/en-US/docs/Web/CSS/Class_selectors)

### Packages Used

- [mistune](https://pypi.org/project/mistune/): Markdown parser 
    - [docs](https://mistune.lepture.com/en/latest/)

### Project Tools

- [uv](https://github.com/astral-sh/uv#readme) - Environment management (in place of `pip`)
- [Ruff](https://docs.astral.sh/ruff/) - Linter and code formatter
- [pytest](https://docs.pytest.org/en/stable/) - Testing framework
- [build](https://build.pypa.io/en/stable/index.html) - Python packaging build frontend
- [twine](https://twine.readthedocs.io/en/latest/) - Utility for publishing Python packages
- [Just](https://github.com/casey/just#readme) - Command runner
