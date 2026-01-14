"""
Parser for Victoria 2 save files (Paradox script format).
"""

import re
from typing import Any


class SaveParser:
    """Parser for Paradox save file format."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def parse(self) -> dict:
        """Parse the entire save file into a dictionary."""
        return self._parse_block_contents()

    def _skip_whitespace(self):
        """Skip whitespace and comments."""
        while self.pos < self.length:
            if self.text[self.pos] in ' \t\n\r':
                self.pos += 1
            elif self.text[self.pos] == '#':
                # Skip comment until end of line
                while self.pos < self.length and self.text[self.pos] != '\n':
                    self.pos += 1
            else:
                break

    def _peek(self) -> str | None:
        """Peek at current character."""
        if self.pos < self.length:
            return self.text[self.pos]
        return None

    def _read_token(self) -> str:
        """Read a token (key or unquoted value)."""
        start = self.pos
        while self.pos < self.length:
            c = self.text[self.pos]
            if c in ' \t\n\r={}#':
                break
            self.pos += 1
        return self.text[start:self.pos]

    def _read_quoted_string(self) -> str:
        """Read a quoted string."""
        self.pos += 1  # Skip opening quote
        start = self.pos
        while self.pos < self.length:
            c = self.text[self.pos]
            if c == '"':
                result = self.text[start:self.pos]
                self.pos += 1  # Skip closing quote
                return result
            self.pos += 1
        return self.text[start:self.pos]

    def _parse_value(self) -> Any:
        """Parse a value (string, number, or block)."""
        self._skip_whitespace()
        c = self._peek()

        if c == '"':
            return self._read_quoted_string()
        elif c == '{':
            return self._parse_block()
        else:
            token = self._read_token()
            # Try to convert to number
            try:
                if '.' in token:
                    return float(token)
                return int(token)
            except ValueError:
                # Check for boolean
                if token.lower() == 'yes':
                    return True
                elif token.lower() == 'no':
                    return False
                return token

    def _parse_block(self) -> dict | list:
        """Parse a block {...}."""
        self.pos += 1  # Skip '{'
        self._skip_whitespace()

        # Check if this is a simple list (no = signs at top level)
        # We need to peek ahead to determine structure
        result = self._parse_block_contents()

        self._skip_whitespace()
        if self._peek() == '}':
            self.pos += 1

        return result

    def _parse_block_contents(self) -> dict | list:
        """Parse contents of a block or root level."""
        # First, try to detect if this is a list or dict
        save_pos = self.pos
        self._skip_whitespace()

        # Check first element to guess structure
        is_list = False
        if self._peek() == '}':
            return {}

        if self._peek() == '"':
            # Could be list of strings or key-value
            self._read_quoted_string()
            self._skip_whitespace()
            if self._peek() != '=':
                is_list = True
        elif self._peek() == '{':
            # List of blocks (anonymous)
            is_list = True
        elif self._peek() and self._peek() not in '{}':
            token = self._read_token()
            self._skip_whitespace()
            if self._peek() != '=':
                # It's a list
                is_list = True

        # Reset position
        self.pos = save_pos

        if is_list:
            return self._parse_list()
        else:
            return self._parse_dict()

    def _parse_list(self) -> list:
        """Parse a list of values."""
        result = []
        while True:
            self._skip_whitespace()
            c = self._peek()
            if c is None or c == '}':
                break
            value = self._parse_value()
            result.append(value)
        return result

    def _parse_dict(self) -> dict:
        """Parse a dictionary of key-value pairs."""
        result = {}
        while True:
            self._skip_whitespace()
            c = self._peek()
            if c is None or c == '}':
                break

            # Read key
            if c == '"':
                key = self._read_quoted_string()
            else:
                key = self._read_token()

            if not key:
                break

            self._skip_whitespace()

            # Expect '='
            if self._peek() == '=':
                self.pos += 1
                value = self._parse_value()

                # Handle duplicate keys by converting to list
                if key in result:
                    if isinstance(result[key], list) and not isinstance(value, (dict, list)):
                        result[key].append(value)
                    elif isinstance(result[key], list):
                        result[key].append(value)
                    else:
                        result[key] = [result[key], value]
                else:
                    result[key] = value
            else:
                # No '=' found, might be end of block or malformed
                break

        return result


def parse_save_file(filepath: str) -> dict:
    """Parse a Victoria 2 save file."""
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()
    parser = SaveParser(text)
    return parser.parse()


def fast_extract_sections(filepath: str, sections: list[str]) -> dict:
    """
    Fast extraction of specific top-level sections without full parsing.
    Much faster for large files when only specific data is needed.
    """
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()

    results = {}

    for section in sections:
        # Find section start
        pattern = rf'^{re.escape(section)}='
        match = re.search(pattern, text, re.MULTILINE)
        if not match:
            continue

        start = match.end()

        # Skip whitespace
        while start < len(text) and text[start] in ' \t\n\r':
            start += 1

        if start >= len(text):
            continue

        # Check if it's a block or simple value
        if text[start] == '{':
            # Find matching brace
            brace_count = 1
            pos = start + 1
            while pos < len(text) and brace_count > 0:
                if text[pos] == '{':
                    brace_count += 1
                elif text[pos] == '}':
                    brace_count -= 1
                pos += 1
            section_text = text[start:pos]
        else:
            # Simple value - read until newline
            end = text.find('\n', start)
            if end == -1:
                end = len(text)
            section_text = text[start:end]

        # Parse just this section
        parser = SaveParser(section_text)
        results[section] = parser.parse()

    return results


def iterate_country_sections(filepath: str):
    """
    Generator that yields country data one at a time.
    Memory efficient for large files.
    """
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()

    # Country tags are 3 uppercase letters followed by =
    pattern = r'^([A-Z]{3})=\n\{'

    for match in re.finditer(pattern, text, re.MULTILINE):
        tag = match.group(1)
        start = match.end() - 1  # Include the '{'

        # Find matching brace
        brace_count = 1
        pos = start + 1
        while pos < len(text) and brace_count > 0:
            if text[pos] == '{':
                brace_count += 1
            elif text[pos] == '}':
                brace_count -= 1
            pos += 1

        section_text = text[start:pos]
        parser = SaveParser(section_text)
        yield tag, parser.parse()


def iterate_province_sections(filepath: str):
    """
    Generator that yields province data one at a time.
    Memory efficient for large files.
    """
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()

    # Province IDs are numbers followed by = and {
    # They appear after the worldmarket section
    pattern = r'^(\d+)=\n\{\n\tname='

    for match in re.finditer(pattern, text, re.MULTILINE):
        province_id = int(match.group(1))
        start = match.start() + len(match.group(1)) + 2  # After '=\n'

        # Find matching brace
        brace_count = 1
        pos = start + 1
        while pos < len(text) and brace_count > 0:
            if text[pos] == '{':
                brace_count += 1
            elif text[pos] == '}':
                brace_count -= 1
            pos += 1

        section_text = text[start:pos]
        parser = SaveParser(section_text)
        yield province_id, parser.parse()
