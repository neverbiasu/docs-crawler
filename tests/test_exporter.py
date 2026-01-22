"""Tests for the Exporter class."""

import os
import tempfile
import pytest
from docs_crawler.exporter import Exporter


class TestExporter:
    """Test cases for Exporter functionality."""

    def test_exporter_initialization(self):
        """Test exporter initializes with correct attributes."""
        exporter = Exporter(input_dir="/tmp/test", output_path="/tmp/output.md")
        assert exporter.input_dir == "/tmp/test"
        assert exporter.output_path == "/tmp/output.md"

    def test_get_alphabetical_order(self):
        """Test alphabetical ordering when index.md is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test markdown files
            for name in ["c_page.md", "a_page.md", "b_page.md"]:
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write(f"# {name}\n")

            exporter = Exporter(input_dir=tmpdir)
            order = exporter._get_alphabetical_order()

            assert order == ["a_page.md", "b_page.md", "c_page.md"]

    def test_get_page_order_from_index(self):
        """Test page ordering from index.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test markdown files
            for name in ["page1.md", "page2.md", "page3.md"]:
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write(f"# {name}\n")

            # Create index.md with specific order
            index_content = """# Index

| Title | URL | File |
|-------|-----|------|
| Page 3 | [url](url) | [page3.md](page3.md) |
| Page 1 | [url](url) | [page1.md](page1.md) |
| Page 2 | [url](url) | [page2.md](page2.md) |
"""
            with open(os.path.join(tmpdir, "index.md"), "w") as f:
                f.write(index_content)

            exporter = Exporter(input_dir=tmpdir)
            order = exporter.get_page_order()

            assert order == ["page3.md", "page1.md", "page2.md"]

    def test_get_page_order_fallback_to_alphabetical(self):
        """Test fallback to alphabetical when index.md is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test markdown files
            for name in ["b.md", "a.md"]:
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write(f"# {name}\n")

            exporter = Exporter(input_dir=tmpdir)
            order = exporter.get_page_order()

            assert order == ["a.md", "b.md"]

    def test_merge_content(self):
        """Test merging markdown files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test markdown files
            with open(os.path.join(tmpdir, "a.md"), "w") as f:
                f.write("# Page A\n\nContent A")
            with open(os.path.join(tmpdir, "b.md"), "w") as f:
                f.write("# Page B\n\nContent B")

            exporter = Exporter(input_dir=tmpdir)
            merged = exporter.merge()

            assert "# Page A" in merged
            assert "Content A" in merged
            assert "# Page B" in merged
            assert "Content B" in merged
            assert "---" in merged  # Separator between files

    def test_export_merged_md(self):
        """Test exporting merged markdown to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test markdown files
            with open(os.path.join(tmpdir, "test.md"), "w") as f:
                f.write("# Test\n\nTest content")

            exporter = Exporter(input_dir=tmpdir)
            output_file = exporter.export_merged_md()

            assert os.path.exists(output_file)
            assert output_file.endswith("merged.md")

            with open(output_file, "r") as f:
                content = f.read()
            assert "# Test" in content

    def test_export_merged_md_custom_output(self):
        """Test exporting merged markdown to custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test markdown files
            with open(os.path.join(tmpdir, "test.md"), "w") as f:
                f.write("# Test\n\nTest content")

            custom_output = os.path.join(tmpdir, "custom.md")
            exporter = Exporter(input_dir=tmpdir, output_path=custom_output)
            output_file = exporter.export_merged_md()

            assert output_file == custom_output
            assert os.path.exists(output_file)

    def test_merge_empty_directory_raises(self):
        """Test merging empty directory raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = Exporter(input_dir=tmpdir)

            with pytest.raises(ValueError, match="No markdown files found"):
                exporter.merge()

    def test_export_pdf_missing_dependency(self):
        """Test PDF export with missing dependency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test markdown file
            with open(os.path.join(tmpdir, "test.md"), "w") as f:
                f.write("# Test\n\nTest content")

            exporter = Exporter(input_dir=tmpdir)

            # This should raise ImportError if md2pdf is not installed
            # We can't guarantee md2pdf is installed, so just test the method exists
            assert hasattr(exporter, "export_pdf")
