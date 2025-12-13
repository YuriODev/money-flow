"""XML prompt parsing utilities.

This module provides utilities for parsing XML-formatted prompts.
All prompt files are stored in src/agent/prompts/ directory.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


class XMLPromptParser:
    """Parse XML prompt files for the agentic interface.

    This class loads and parses XML files from the prompts directory,
    providing structured access to system prompts, command patterns,
    currency configuration, and response templates.

    Attributes:
        prompts_dir: Path to the prompts directory

    Example:
        >>> parser = XMLPromptParser()
        >>> system_prompt = parser.parse_system_prompt()
        >>> system_prompt['role']
        'subscription_assistant'
    """

    def __init__(self, prompts_dir: str | None = None):
        """Initialize XML parser with prompts directory.

        Args:
            prompts_dir: Path to prompts directory (default: src/agent/prompts)
        """
        if prompts_dir is None:
            # Default to src/agent/prompts relative to this file
            self.prompts_dir = Path(__file__).parent.parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

    def parse_system_prompt(self) -> dict[str, Any]:
        """Parse system.xml and return structured system prompt data.

        Returns:
            Dictionary with role, description, capabilities, and guidelines

        Example:
            >>> parser = XMLPromptParser()
            >>> data = parser.parse_system_prompt()
            >>> data['role']
            'subscription_assistant'
            >>> len(data['capabilities'])
            5
        """
        tree = ET.parse(self.prompts_dir / "system.xml")
        root = tree.getroot()

        return {
            "role": root.find("role").text.strip(),
            "description": root.find("description").text.strip(),
            "capabilities": [cap.text.strip() for cap in root.findall("capabilities/capability")],
            "guidelines": [guide.text.strip() for guide in root.findall("guidelines/guideline")],
        }

    def parse_command_patterns(self) -> dict[str, Any]:
        """Parse command_patterns.xml and return structured patterns data.

        Returns:
            Dictionary mapping pattern types to their examples and extraction rules

        Example:
            >>> parser = XMLPromptParser()
            >>> patterns = parser.parse_command_patterns()
            >>> 'create' in patterns
            True
            >>> len(patterns['create']['examples'])
            7
        """
        tree = ET.parse(self.prompts_dir / "command_patterns.xml")
        root = tree.getroot()

        patterns = {}
        for pattern in root.findall("pattern"):
            pattern_type = pattern.get("type")
            patterns[pattern_type] = {
                "examples": [ex.text.strip() for ex in pattern.findall("examples/example")],
                "extraction": {},
            }

            # Parse extraction fields
            extraction_elem = pattern.find("extraction")
            if extraction_elem is not None:
                for field in extraction_elem.findall("field"):
                    field_name = field.get("name")
                    patterns[pattern_type]["extraction"][field_name] = {
                        "required": field.get("required") == "true",
                        "default": field.get("default"),
                        "description": field.text.strip(),
                    }

        return patterns

    def parse_currency_config(self) -> dict[str, Any]:
        """Parse currency.xml and return currency configuration.

        Returns:
            Dictionary with default currency, supported currencies, and detection rules

        Example:
            >>> parser = XMLPromptParser()
            >>> config = parser.parse_currency_config()
            >>> config['default_currency']
            'GBP'
            >>> len(config['supported_currencies'])
            3
        """
        tree = ET.parse(self.prompts_dir / "currency.xml")
        root = tree.getroot()

        return {
            "default_currency": root.find("default_currency").text.strip(),
            "supported_currencies": [
                {
                    "code": curr.get("code"),
                    "symbol": curr.get("symbol"),
                    "name": curr.get("name"),
                }
                for curr in root.findall("supported_currencies/currency")
            ],
            "detection_rules": [
                rule.text.strip() for rule in root.findall("currency_detection/rule")
            ],
        }

    def parse_response_templates(self) -> dict[str, str]:
        """Parse response_templates.xml and return templates.

        Returns:
            Dictionary mapping template types to format strings

        Example:
            >>> parser = XMLPromptParser()
            >>> templates = parser.parse_response_templates()
            >>> 'success_create' in templates
            True
        """
        tree = ET.parse(self.prompts_dir / "response_templates.xml")
        root = tree.getroot()

        return {
            template.get("type"): template.find("format").text.strip()
            for template in root.findall("template")
        }

    def parse_command_prompt_template(self) -> dict[str, Any]:
        """Parse command_prompt_template.xml for building command prompts.

        Returns:
            Dictionary with template parts for constructing command prompts

        Example:
            >>> parser = XMLPromptParser()
            >>> template = parser.parse_command_prompt_template()
            >>> 'header' in template
            True
        """
        tree = ET.parse(self.prompts_dir / "command_prompt_template.xml")
        root = tree.getroot()

        pattern_format = root.find("pattern_format")

        return {
            "header": root.find("header").text.strip(),
            "user_command_format": root.find("user_command_format").text.strip(),
            "patterns_header": root.find("patterns_header").text.strip(),
            "pattern_format": {
                "type_header": pattern_format.find("type_header").text.strip(),
                "examples_header": pattern_format.find("examples_header").text.strip(),
                "example_format": pattern_format.find("example_format").text.strip(),
                "extraction_header": pattern_format.find("extraction_header").text.strip(),
                "field_format": pattern_format.find("field_format").text.strip(),
            },
            "response_format": root.find("response_format").text.strip(),
        }
