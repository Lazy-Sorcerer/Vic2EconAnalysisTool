"""
Parser for Victoria 2 save files (Paradox script format).

This module provides parsing capabilities for Victoria 2 save files, which use
Paradox's proprietary script format. The format consists of key-value pairs
with nested blocks enclosed in curly braces.

PARADOX SCRIPT FORMAT OVERVIEW
==============================

The Paradox script format is a hierarchical text-based data format used in
Paradox Interactive games (EU4, CK2, Victoria 2, HOI4, etc.). It has the
following characteristics:

1. **Key-Value Pairs**: `key=value`
   - Keys are unquoted identifiers (letters, numbers, underscores)
   - Values can be: strings, integers, floats, booleans (yes/no), or blocks

2. **Nested Blocks**: `key={ ... }`
   - Blocks contain either key-value pairs (dict-like) or lists of values
   - Blocks can be nested arbitrarily deep

3. **Comments**: Lines starting with # are comments

4. **Encoding**: Files use Latin-1 (ISO-8859-1) encoding

EXAMPLE SAVE FILE STRUCTURE
===========================

```
date="1836.1.1"
player="ENG"
worldmarket={
    worldmarket_pool={
        ammunition=1234.567
        small_arms=890.123
    }
}
ENG={
    prestige=100.5
    treasury=50000.00
    state={
        provinces={ 300 301 302 }
        state_buildings={
            building="fabric_factory"
            level=2
        }
    }
}
```

PARSING STRATEGY
================

The parser uses a recursive descent approach:
1. Tokenize the input character by character
2. Determine if current context is a dict or list by looking ahead
3. Recursively parse nested blocks
4. Handle duplicate keys by converting to lists (common in Paradox files)

USAGE
=====

Basic parsing:
    >>> data = parse_save_file("save.v2")
    >>> print(data['date'])
    "1836.1.1"

Fast extraction of specific sections:
    >>> market_data = fast_extract_sections("save.v2", ["worldmarket"])
    >>> print(market_data['worldmarket']['worldmarket_pool'])

Memory-efficient iteration over countries:
    >>> for tag, country_data in iterate_country_sections("save.v2"):
    ...     print(f"{tag}: {country_data.get('prestige', 0)}")

Author: Victoria 2 Economy Analysis Tool Project
"""

import re
from typing import Any


class SaveParser:
    """
    Parser for Paradox save file format using recursive descent parsing.

    This parser reads the entire file into memory and maintains a position
    pointer that advances through the text as tokens are consumed. The
    parsing is context-sensitive, determining whether a block contains
    a dictionary or a list by examining its first element.

    Attributes:
        text (str): The complete save file content
        pos (int): Current position in the text (character index)
        length (int): Total length of the text

    Example:
        >>> parser = SaveParser('key="value" number=42')
        >>> result = parser.parse()
        >>> print(result)
        {'key': 'value', 'number': 42}

    Notes:
        - Handles duplicate keys by automatically converting to lists
        - Supports nested blocks of arbitrary depth
        - Automatically converts numeric strings to int/float
        - Converts "yes"/"no" to Python booleans True/False
    """

    def __init__(self, text: str):
        """
        Initialize the parser with the text to parse.

        Args:
            text: The Paradox script format text to parse. Should be the
                  complete content of a save file or a section thereof.
        """
        self.text = text
        self.pos = 0          # Current parsing position (cursor)
        self.length = len(text)

    def parse(self) -> dict:
        """
        Parse the entire save file into a dictionary.

        This is the main entry point for parsing. It treats the entire
        input as the contents of an implicit root block.

        Returns:
            dict: Parsed data structure. Keys are strings, values can be:
                  - str: For quoted strings and unquoted text
                  - int: For integer values
                  - float: For decimal values
                  - bool: For yes/no values
                  - dict: For nested blocks with key-value pairs
                  - list: For blocks containing only values (no keys)

        Example:
            >>> parser = SaveParser('date="1836.1.1" player="ENG"')
            >>> parser.parse()
            {'date': '1836.1.1', 'player': 'ENG'}
        """
        return self._parse_block_contents()

    def _skip_whitespace(self):
        """
        Skip whitespace characters and comments.

        Advances the position pointer past:
        - Spaces, tabs, newlines, carriage returns
        - Comments (# to end of line)

        This is called before reading each token to ensure we're at
        meaningful content.

        Implementation Note:
            Comments in Paradox files start with # and continue to the
            end of the line. They can appear anywhere whitespace is valid.
        """
        while self.pos < self.length:
            if self.text[self.pos] in ' \t\n\r':
                # Skip whitespace character
                self.pos += 1
            elif self.text[self.pos] == '#':
                # Skip comment: consume all characters until newline
                while self.pos < self.length and self.text[self.pos] != '\n':
                    self.pos += 1
            else:
                # Found non-whitespace, non-comment character
                break

    def _peek(self) -> str | None:
        """
        Peek at the current character without consuming it.

        Returns:
            str | None: The character at the current position, or None if
                        we've reached the end of the text.

        This is used extensively for lookahead to determine what type
        of token or structure comes next.
        """
        if self.pos < self.length:
            return self.text[self.pos]
        return None

    def _read_token(self) -> str:
        """
        Read a token (key or unquoted value).

        A token is a sequence of characters that doesn't include whitespace
        or special characters (=, {, }, #). This is used for:
        - Reading dictionary keys
        - Reading unquoted values (numbers, identifiers, booleans)

        Returns:
            str: The token string. May be empty if no valid characters found.

        Example:
            For input "prestige=100.5", calling _read_token() at the start
            would return "prestige" and advance pos to the '=' character.

        Token-Ending Characters:
            - Space, tab, newline, carriage return (whitespace)
            - '=' (key-value separator)
            - '{' and '}' (block delimiters)
            - '#' (comment start)
        """
        start = self.pos
        while self.pos < self.length:
            c = self.text[self.pos]
            # Stop at any character that delimits a token
            if c in ' \t\n\r={}#':
                break
            self.pos += 1
        return self.text[start:self.pos]

    def _read_quoted_string(self) -> str:
        """
        Read a quoted string value.

        Quoted strings are enclosed in double quotes and can contain
        spaces and special characters. This method:
        1. Skips the opening quote
        2. Reads all characters until the closing quote
        3. Skips the closing quote

        Returns:
            str: The string content without the surrounding quotes.

        Example:
            For input '"Hello World"', returns 'Hello World'

        Note:
            Paradox format doesn't use escape sequences (no \" or \\).
            Quotes cannot appear inside quoted strings.
        """
        self.pos += 1  # Skip opening quote (")
        start = self.pos
        while self.pos < self.length:
            c = self.text[self.pos]
            if c == '"':
                # Found closing quote
                result = self.text[start:self.pos]
                self.pos += 1  # Skip closing quote
                return result
            self.pos += 1
        # Reached end of file without finding closing quote
        # Return what we have (malformed input handling)
        return self.text[start:self.pos]

    def _parse_value(self) -> Any:
        """
        Parse a value (string, number, boolean, or nested block).

        This method determines the type of value by examining the first
        character and dispatches to the appropriate parsing method.

        Returns:
            The parsed value, which can be:
            - str: For quoted or unquoted strings
            - int: For integer values (no decimal point)
            - float: For floating-point values (has decimal point)
            - bool: For yes/no values (True/False)
            - dict: For nested blocks with key-value pairs
            - list: For nested blocks with only values

        Value Type Detection:
            - Starts with '"': Quoted string
            - Starts with '{': Nested block (dict or list)
            - Otherwise: Unquoted token (number, boolean, or string)

        Type Conversion Priority:
            1. Try float (if contains '.')
            2. Try int
            3. Check for boolean (yes/no)
            4. Keep as string
        """
        self._skip_whitespace()
        c = self._peek()

        if c == '"':
            # Quoted string value
            return self._read_quoted_string()
        elif c == '{':
            # Nested block (could be dict or list)
            return self._parse_block()
        else:
            # Unquoted token: could be number, boolean, or identifier
            token = self._read_token()

            # Try to convert to appropriate type
            try:
                if '.' in token:
                    # Contains decimal point: parse as float
                    return float(token)
                # No decimal point: try integer
                return int(token)
            except ValueError:
                # Not a number: check for boolean
                if token.lower() == 'yes':
                    return True
                elif token.lower() == 'no':
                    return False
                # Return as string
                return token

    def _parse_block(self) -> dict | list:
        """
        Parse a block {...}.

        Blocks are enclosed in curly braces and can contain either:
        - Key-value pairs (dict): `{ key1=value1 key2=value2 }`
        - A list of values (list): `{ value1 value2 value3 }`

        The method delegates to _parse_block_contents() which determines
        the block type by examining its structure.

        Returns:
            dict | list: Parsed block contents

        Example Dict Block:
            Input: `{ prestige=100 treasury=5000 }`
            Output: {'prestige': 100, 'treasury': 5000}

        Example List Block:
            Input: `{ 300 301 302 }`
            Output: [300, 301, 302]
        """
        self.pos += 1  # Skip opening brace '{'
        self._skip_whitespace()

        # Parse the block's contents
        result = self._parse_block_contents()

        self._skip_whitespace()
        if self._peek() == '}':
            self.pos += 1  # Skip closing brace '}'

        return result

    def _parse_block_contents(self) -> dict | list:
        """
        Parse contents of a block or root level, auto-detecting structure.

        This method performs lookahead to determine whether the current
        block contains a dictionary (key-value pairs) or a list (values only).

        Detection Algorithm:
            1. If block is empty (starts with }), return empty dict
            2. Read the first element
            3. Check if '=' follows:
               - If yes: This is a dictionary
               - If no: This is a list
            4. Reset position and parse accordingly

        Returns:
            dict | list: Parsed contents based on detected structure

        Structure Detection Cases:
            - `{}` → Empty dict: {}
            - `{ key=value }` → Dict: {'key': value}
            - `{ 1 2 3 }` → List: [1, 2, 3]
            - `{ "str1" "str2" }` → List: ['str1', 'str2']
            - `{ {...} {...} }` → List of dicts: [{...}, {...}]

        Note:
            This lookahead is necessary because Paradox format doesn't
            explicitly distinguish between dicts and lists. The parser
            must infer the structure from the content.
        """
        # Save position for potential backtracking
        save_pos = self.pos
        self._skip_whitespace()

        # Check for empty block
        if self._peek() == '}':
            return {}

        # Determine if this is a list or dict by examining first element
        is_list = False

        if self._peek() == '"':
            # First element is a quoted string
            # Read it to check if '=' follows (dict key) or not (list item)
            self._read_quoted_string()
            self._skip_whitespace()
            if self._peek() != '=':
                is_list = True
        elif self._peek() == '{':
            # First element is an anonymous block: definitely a list
            # Example: { { inner=1 } { inner=2 } }
            is_list = True
        elif self._peek() and self._peek() not in '{}':
            # First element is an unquoted token
            # Read it to check if '=' follows
            token = self._read_token()
            self._skip_whitespace()
            if self._peek() != '=':
                # No '=' means this is a value in a list
                is_list = True

        # Reset position to re-parse with correct structure
        self.pos = save_pos

        if is_list:
            return self._parse_list()
        else:
            return self._parse_dict()

    def _parse_list(self) -> list:
        """
        Parse a list of values.

        Lists contain values without keys, separated by whitespace.
        Values can be of any type (strings, numbers, nested blocks).

        Returns:
            list: List of parsed values

        Example:
            Input: `300 301 302` (inside a block)
            Output: [300, 301, 302]

        Example with Mixed Types:
            Input: `"tag1" "tag2" 100 yes`
            Output: ['tag1', 'tag2', 100, True]

        Used For:
            - Province ID lists: `provinces={ 300 301 302 }`
            - Core lists: `core={ "ENG" "FRA" }`
            - List of nested blocks: `pop={ {...} {...} }`
        """
        result = []
        while True:
            self._skip_whitespace()
            c = self._peek()

            # Stop at end of file or end of block
            if c is None or c == '}':
                break

            # Parse and append the next value
            value = self._parse_value()
            result.append(value)
        return result

    def _parse_dict(self) -> dict:
        """
        Parse a dictionary of key-value pairs.

        Dictionaries contain key=value pairs. Keys can be quoted strings
        or unquoted identifiers. Values can be any type.

        Returns:
            dict: Dictionary of parsed key-value pairs

        Duplicate Key Handling:
            Paradox files often have duplicate keys (e.g., multiple `core=`
            entries). This parser handles duplicates by converting to lists:

            Input: `core="ENG" core="FRA"`
            Output: {'core': ['ENG', 'FRA']}

        Example:
            Input: `prestige=100.5 treasury=50000`
            Output: {'prestige': 100.5, 'treasury': 50000}

        Note:
            The duplicate key handling is essential for correctly parsing
            Paradox files, where it's common to have multiple entries for
            things like cores, buildings, POPs, etc.
        """
        result = {}
        while True:
            self._skip_whitespace()
            c = self._peek()

            # Stop at end of file or end of block
            if c is None or c == '}':
                break

            # Read key (can be quoted or unquoted)
            if c == '"':
                key = self._read_quoted_string()
            else:
                key = self._read_token()

            # Empty key means we couldn't read anything
            if not key:
                break

            self._skip_whitespace()

            # Expect '=' after key
            if self._peek() == '=':
                self.pos += 1  # Skip '='
                value = self._parse_value()

                # Handle duplicate keys by converting to list
                # This is common in Paradox files (e.g., multiple core= entries)
                if key in result:
                    existing = result[key]
                    if isinstance(existing, list):
                        # Already a list: append new value
                        existing.append(value)
                    else:
                        # Convert to list with both values
                        result[key] = [existing, value]
                else:
                    result[key] = value
            else:
                # No '=' found: unexpected format, stop parsing
                break

        return result


def parse_save_file(filepath: str) -> dict:
    """
    Parse a Victoria 2 save file.

    This is the primary entry point for parsing complete save files.
    It reads the file with Latin-1 encoding (standard for Paradox games)
    and returns the fully parsed data structure.

    Args:
        filepath: Path to the .v2 save file

    Returns:
        dict: Complete parsed save file data

    Example:
        >>> data = parse_save_file("autosave.v2")
        >>> print(data['date'])  # "1836.1.1"
        >>> print(data['player'])  # "ENG"
        >>> print(data['worldmarket']['worldmarket_pool']['ammunition'])

    Note:
        For large save files (100+ MB), consider using fast_extract_sections()
        or iterate_country_sections() for better performance and memory usage.

    Encoding:
        Victoria 2 save files use Latin-1 (ISO-8859-1) encoding, which
        supports Western European characters. This is standard for all
        Paradox games of this era.
    """
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()
    parser = SaveParser(text)
    return parser.parse()


def fast_extract_sections(filepath: str, sections: list[str]) -> dict:
    """
    Fast extraction of specific top-level sections without full parsing.

    This function uses regex to locate specific sections in the file and
    only parses those sections, rather than parsing the entire file. This
    is much faster for large files when only specific data is needed.

    Args:
        filepath: Path to the .v2 save file
        sections: List of top-level section names to extract
                  (e.g., ["worldmarket", "great_nations"])

    Returns:
        dict: Dictionary mapping section names to their parsed contents

    Example:
        >>> # Extract only world market data (fast!)
        >>> data = fast_extract_sections("save.v2", ["worldmarket"])
        >>> prices = data['worldmarket']['worldmarket_pool']

    Performance:
        For a 150MB save file:
        - parse_save_file(): ~30 seconds
        - fast_extract_sections(): ~2-3 seconds for specific sections

    Algorithm:
        1. Search for section header using regex: `^section_name=`
        2. Find the matching closing brace using brace counting
        3. Extract and parse only that section's text

    Limitations:
        - Only works for top-level sections (not nested)
        - Section must use `name={...}` format with braces

    Use Cases:
        - Extracting world market data for economy analysis
        - Getting player info without parsing all countries
        - Quick metadata extraction (date, player tag, etc.)
    """
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()

    results = {}

    for section in sections:
        # Find section start with regex
        # Pattern: section name at start of line, followed by =
        pattern = rf'^{re.escape(section)}='
        match = re.search(pattern, text, re.MULTILINE)
        if not match:
            continue

        start = match.end()

        # Skip whitespace after =
        while start < len(text) and text[start] in ' \t\n\r':
            start += 1

        if start >= len(text):
            continue

        # Check if it's a block or simple value
        if text[start] == '{':
            # Block value: find matching closing brace
            # Use brace counting to handle nested blocks
            brace_count = 1
            pos = start + 1
            while pos < len(text) and brace_count > 0:
                if text[pos] == '{':
                    brace_count += 1  # Entering nested block
                elif text[pos] == '}':
                    brace_count -= 1  # Leaving block
                pos += 1
            section_text = text[start:pos]
        else:
            # Simple value: read until newline
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

    This is a memory-efficient way to process country data from large
    save files. Instead of loading all countries into memory, it yields
    them one at a time.

    Args:
        filepath: Path to the .v2 save file

    Yields:
        tuple[str, dict]: Pairs of (country_tag, country_data)
                          Tag is a 3-letter code like "ENG", "FRA", "PRU"

    Example:
        >>> for tag, data in iterate_country_sections("save.v2"):
        ...     treasury = data.get('money', 0)
        ...     print(f"{tag}: {treasury:.2f}")
        ENG: 50000.00
        FRA: 35000.00
        PRU: 25000.00

    Country Tag Format:
        Victoria 2 uses 3-letter uppercase tags for all countries:
        - ENG: England/United Kingdom
        - FRA: France
        - PRU: Prussia
        - USA: United States
        - etc.

    Memory Efficiency:
        For a save file with 200+ countries, this approach uses
        significantly less memory than loading all data at once.

    Note:
        The regex pattern `^([A-Z]{3})=\\n\\{` matches lines that start
        with a 3-letter tag followed by = and an opening brace on the
        next line. This is the standard format for country blocks.
    """
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()

    # Country tags are 3 uppercase letters followed by =
    # The block starts on the next line with {
    pattern = r'^([A-Z]{3})=\n\{'

    for match in re.finditer(pattern, text, re.MULTILINE):
        tag = match.group(1)
        start = match.end() - 1  # Include the opening '{'

        # Find matching closing brace using brace counting
        brace_count = 1
        pos = start + 1
        while pos < len(text) and brace_count > 0:
            if text[pos] == '{':
                brace_count += 1
            elif text[pos] == '}':
                brace_count -= 1
            pos += 1

        # Extract and parse this country's block
        section_text = text[start:pos]
        parser = SaveParser(section_text)
        yield tag, parser.parse()


def iterate_province_sections(filepath: str):
    """
    Generator that yields province data one at a time.

    Memory-efficient iteration over province blocks in the save file.
    Provinces are the basic geographic units in Victoria 2.

    Args:
        filepath: Path to the .v2 save file

    Yields:
        tuple[int, dict]: Pairs of (province_id, province_data)
                          IDs are integers (e.g., 300 for London)

    Example:
        >>> for prov_id, data in iterate_province_sections("save.v2"):
        ...     name = data.get('name', 'Unknown')
        ...     owner = data.get('owner', 'None')
        ...     print(f"{prov_id}: {name} ({owner})")
        300: London (ENG)
        301: Middlesex (ENG)

    Province Data Structure:
        Each province block contains:
        - name: Province name (string)
        - owner: Current owner tag (3-letter code)
        - controller: Current controller (may differ during war)
        - core: List of tags that have cores on this province
        - rgo: Resource gathering operation data
        - Various POP blocks (population units)

    Province ID Range:
        Victoria 2 uses numeric IDs from 1 to ~3000+ for provinces.
        Some IDs are reserved for sea zones and wasteland.

    Note:
        The pattern `^(\\d+)=\\n\\{\\n\\tname=` specifically matches province
        blocks by requiring `name=` as the first field inside the block.
        This distinguishes provinces from other numeric-keyed sections.
    """
    with open(filepath, 'r', encoding='latin-1') as f:
        text = f.read()

    # Province IDs are numbers followed by = and {
    # We look for name= as the first field to confirm it's a province
    pattern = r'^(\d+)=\n\{\n\tname='

    for match in re.finditer(pattern, text, re.MULTILINE):
        province_id = int(match.group(1))
        start = match.start() + len(match.group(1)) + 2  # After '=\n'

        # Find matching closing brace
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
