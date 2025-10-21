import csv
import io
from typing import List, Dict, Any, Tuple
import codecs

class FAQCSVParserError(Exception):
    """Exception raised for errors during FAQ CSV parsing."""
    pass

class FAQCSVParser:
    """
    Parser for FAQ CSV files with BOM support.
    Expects CSV with 'question' and 'answer' columns.
    """

    REQUIRED_COLUMNS = ['question', 'answer']

    @staticmethod
    def parse(content: bytes) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Parse FAQ CSV content with BOM support.

        Args:
            content: Raw bytes from CSV file

        Returns:
            Tuple of (list of FAQ pairs, list of validation errors)

        Raises:
            FAQCSVParserError: If parsing fails or critical validation errors occur
        """
        # Handle BOM - try UTF-8 with BOM first
        text_content = None

        # Try UTF-8 with BOM
        if content.startswith(codecs.BOM_UTF8):
            text_content = content.decode('utf-8-sig')
        # Try UTF-16 with BOM
        elif content.startswith(codecs.BOM_UTF16_LE) or content.startswith(codecs.BOM_UTF16_BE):
            text_content = content.decode('utf-16')
        # Try UTF-32 with BOM
        elif content.startswith(codecs.BOM_UTF32_LE) or content.startswith(codecs.BOM_UTF32_BE):
            text_content = content.decode('utf-32')
        else:
            # No BOM, try UTF-8
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                raise FAQCSVParserError("Unable to decode CSV file. Please ensure it's UTF-8 encoded.")

        # Parse CSV
        try:
            csv_reader = csv.DictReader(io.StringIO(text_content))

            # Validate headers
            if csv_reader.fieldnames is None:
                raise FAQCSVParserError("CSV file is empty or has no headers.")

            # Normalize headers (lowercase and strip whitespace)
            normalized_headers = [h.lower().strip() for h in csv_reader.fieldnames]

            # Check for required columns
            missing_columns = []
            for required_col in FAQCSVParser.REQUIRED_COLUMNS:
                if required_col not in normalized_headers:
                    missing_columns.append(required_col)

            if missing_columns:
                raise FAQCSVParserError(
                    f"Missing required columns: {', '.join(missing_columns)}. "
                    f"CSV must have headers: {', '.join(FAQCSVParser.REQUIRED_COLUMNS)}"
                )

            # Create mapping of normalized to original headers
            header_mapping = {}
            for original_header in csv_reader.fieldnames:
                normalized = original_header.lower().strip()
                if normalized in FAQCSVParser.REQUIRED_COLUMNS:
                    header_mapping[normalized] = original_header

            # Parse rows
            faq_pairs = []
            errors = []
            row_num = 1  # Start at 1 (header is row 0)

            for row in csv_reader:
                row_num += 1

                # Extract question and answer using the mapping
                question = row.get(header_mapping['question'], '').strip()
                answer = row.get(header_mapping['answer'], '').strip()

                # Skip completely empty rows
                if not question and not answer:
                    continue

                # Validate row
                row_errors = FAQCSVParser._validate_row(question, answer, row_num)

                if row_errors:
                    errors.extend(row_errors)
                    # Still add the pair, but flag it
                    if question or answer:  # Only add if at least one field has content
                        faq_pairs.append({
                            "question": question,
                            "answer": answer,
                            "row_number": row_num,
                            "has_errors": True
                        })
                else:
                    faq_pairs.append({
                        "question": question,
                        "answer": answer,
                        "row_number": row_num,
                        "has_errors": False
                    })

            if not faq_pairs:
                raise FAQCSVParserError("CSV file contains no valid FAQ pairs.")

            return faq_pairs, errors

        except csv.Error as e:
            raise FAQCSVParserError(f"CSV parsing error: {str(e)}")
        except Exception as e:
            if isinstance(e, FAQCSVParserError):
                raise
            raise FAQCSVParserError(f"Unexpected error while parsing CSV: {str(e)}")

    @staticmethod
    def _validate_row(question: str, answer: str, row_num: int) -> List[str]:
        """
        Validate a single FAQ row.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if not question:
            errors.append(f"Row {row_num}: Missing question")

        if not answer:
            errors.append(f"Row {row_num}: Missing answer")

        # Check for reasonable length limits
        if len(question) > 5000:
            errors.append(f"Row {row_num}: Question exceeds maximum length of 5000 characters")

        if len(answer) > 10000:
            errors.append(f"Row {row_num}: Answer exceeds maximum length of 10000 characters")

        return errors

    @staticmethod
    def generate_template() -> str:
        """
        Generate a CSV template with required headers.

        Returns:
            CSV string with headers only
        """
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=FAQCSVParser.REQUIRED_COLUMNS)
        writer.writeheader()
        return output.getvalue()

    @staticmethod
    def validate_before_save(faq_pairs: List[Dict[str, str]], allow_errors: bool = False) -> Tuple[bool, List[str]]:
        """
        Final validation before saving to database.

        Args:
            faq_pairs: List of FAQ pairs to validate
            allow_errors: If False, reject upload with any errors

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        if not faq_pairs:
            errors.append("No FAQ pairs to save")
            return False, errors

        # Check for pairs with errors
        pairs_with_errors = [p for p in faq_pairs if p.get('has_errors', False)]

        if pairs_with_errors and not allow_errors:
            errors.append(f"{len(pairs_with_errors)} FAQ pair(s) have validation errors")
            return False, errors

        # Count valid pairs
        valid_pairs = [p for p in faq_pairs if not p.get('has_errors', False)]

        if not valid_pairs:
            errors.append("No valid FAQ pairs found")
            return False, errors

        return True, []
