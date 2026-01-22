"""Export functionality for docs-crawler."""

import os
import re
import logging

logger = logging.getLogger(__name__)


class Exporter:
    """Export crawled markdown files to various formats."""

    def __init__(self, input_dir, output_path=None):
        """
        Initialize the exporter.

        Args:
            input_dir: Directory containing crawled markdown files
            output_path: Output file path (optional, auto-generated if not provided)
        """
        self.input_dir = input_dir
        self.output_path = output_path

    def get_page_order(self):
        """
        Read index.md and extract page order.

        Returns:
            List of markdown filenames in order
        """
        index_path = os.path.join(self.input_dir, "index.md")

        if not os.path.exists(index_path):
            logger.warning("index.md not found, falling back to alphabetical order")
            return self._get_alphabetical_order()

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse table rows to extract local file references
            # Format: | Title | [url](url) | [file.md](file.md) |
            pattern = r"\[([^\]]+\.md)\]\([^\)]+\.md\)"
            matches = re.findall(pattern, content)

            if not matches:
                logger.warning("No files found in index.md, falling back to alphabetical order")
                return self._get_alphabetical_order()

            # Filter to only existing files
            files = []
            for filename in matches:
                if filename != "index.md" and os.path.exists(
                    os.path.join(self.input_dir, filename)
                ):
                    files.append(filename)

            return files

        except Exception as e:
            logger.warning(f"Error reading index.md: {e}, falling back to alphabetical order")
            return self._get_alphabetical_order()

    def _get_alphabetical_order(self):
        """Get markdown files in alphabetical order."""
        files = []
        for filename in sorted(os.listdir(self.input_dir)):
            if filename.endswith(".md") and filename != "index.md":
                files.append(filename)
        return files

    def merge(self):
        """
        Merge all markdown files in order.

        Returns:
            Merged content as string
        """
        files = self.get_page_order()

        if not files:
            raise ValueError(f"No markdown files found in {self.input_dir}")

        merged_content = []

        for filename in files:
            filepath = os.path.join(self.input_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()

                # Add separator between files
                if merged_content:
                    merged_content.append("\n\n---\n\n")

                merged_content.append(content)
                logger.debug(f"Added {filename} to merged content")

            except Exception as e:
                logger.warning(f"Error reading {filename}: {e}, skipping")

        return "".join(merged_content)

    def export_merged_md(self):
        """
        Write merged markdown to file.

        Returns:
            Path to the output file
        """
        merged_content = self.merge()

        if self.output_path:
            output_file = self.output_path
        else:
            output_file = os.path.join(self.input_dir, "merged.md")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(merged_content)

        logger.info(f"Merged markdown written to {output_file}")
        return output_file

    def export_pdf(self):
        """
        Convert merged markdown to PDF.

        Returns:
            Path to the output PDF file
        """
        try:
            from md2pdf.core import md2pdf as convert_md2pdf
        except ImportError:
            raise ImportError(
                "PDF export requires md2pdf. Install with: pip install docs-crawler[pdf]"
            )

        merged_content = self.merge()

        if self.output_path:
            output_file = self.output_path
        else:
            output_file = os.path.join(self.input_dir, "merged.pdf")

        # Ensure output has .pdf extension
        if not output_file.endswith(".pdf"):
            output_file = output_file.rsplit(".", 1)[0] + ".pdf"

        convert_md2pdf(
            output_file,
            md_content=merged_content,
        )

        logger.info(f"PDF written to {output_file}")
        return output_file
