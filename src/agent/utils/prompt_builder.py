"""Prompt building utilities.

This module provides clean, template-based prompt construction.
"""

from typing import Any


class PromptBuilder:
    """Build prompts from templates and data.

    This class constructs prompts using parsed XML templates,
    eliminating manual string concatenation in the main code.

    Attributes:
        template: Parsed command prompt template
        pattern_fmt: Pattern formatting configuration

    Example:
        >>> builder = PromptBuilder(template_data)
        >>> prompt = builder.build_command_prompt("Add Netflix", patterns)
    """

    def __init__(self, template: dict[str, Any]):
        """Initialize builder with template data.

        Args:
            template: Parsed command prompt template from XMLPromptParser
        """
        self.template = template
        self.pattern_fmt = template["pattern_format"]

    def build_command_prompt(
        self,
        user_command: str,
        patterns: dict[str, Any],
    ) -> str:
        """Build a command parsing prompt from template.

        Args:
            user_command: User's natural language command
            patterns: Parsed command patterns dictionary

        Returns:
            Formatted prompt string for Claude API

        Example:
            >>> prompt = builder.build_command_prompt("Add Netflix £10", patterns)
            >>> "Add Netflix £10" in prompt
            True
        """
        sections = [
            self.template["header"],
            "",
            self.template["user_command_format"].format(user_command=user_command),
            "",
            self.template["patterns_header"],
        ]

        for pattern_type, pattern_data in patterns.items():
            sections.append("")
            sections.append(
                self.pattern_fmt["type_header"].format(pattern_type=pattern_type.upper())
            )
            sections.append(self.pattern_fmt["examples_header"])
            sections.extend(self._format_examples(pattern_data["examples"]))

            if pattern_data["extraction"]:
                sections.append(self.pattern_fmt["extraction_header"])
                sections.extend(self._format_extraction_fields(pattern_data["extraction"]))

        sections.append(self.template["response_format"])

        return "\n".join(sections)

    def _format_examples(self, examples: list[str]) -> list[str]:
        """Format example lines.

        Args:
            examples: List of example strings

        Returns:
            Formatted example lines
        """
        return [self.pattern_fmt["example_format"].format(example=example) for example in examples]

    def _format_extraction_fields(
        self,
        extraction: dict[str, dict[str, Any]],
    ) -> list[str]:
        """Format extraction field lines.

        Args:
            extraction: Dictionary of field configurations

        Returns:
            Formatted field description lines
        """
        lines = []
        for field_name, field_info in extraction.items():
            required = "REQUIRED" if field_info["required"] else "optional"
            default = f" (default: {field_info['default']})" if field_info["default"] else ""
            lines.append(
                self.pattern_fmt["field_format"].format(
                    field_name=field_name,
                    required=required,
                    default=default,
                    description=field_info["description"],
                )
            )
        return lines

    def build_system_prompt(
        self,
        system_data: dict[str, Any],
        currency_config: dict[str, Any],
    ) -> str:
        """Build system prompt from data.

        Args:
            system_data: Parsed system prompt data
            currency_config: Parsed currency configuration

        Returns:
            Formatted system prompt for Claude API
        """
        sections = [
            "<system>",
            f"You are a {system_data['role']}.",
            "",
            system_data["description"],
            "",
            "<capabilities>",
            *[f"- {cap}" for cap in system_data["capabilities"]],
            "</capabilities>",
            "",
            "<guidelines>",
            *[f"- {guide}" for guide in system_data["guidelines"]],
            "</guidelines>",
            "",
            "<currency_information>",
            f"Default currency: {currency_config['default_currency']}",
            "",
            "Supported currencies:",
            *[
                f"- {curr['name']} ({curr['code']}): {curr['symbol']}"
                for curr in currency_config["supported_currencies"]
            ],
            "",
            "Currency detection rules:",
            *[f"- {rule}" for rule in currency_config["detection_rules"]],
            "</currency_information>",
            "</system>",
        ]

        return "\n".join(sections)
