"""Prompt loader using XML-based prompts.

This module loads and formats prompts from XML files for the Claude API.
All prompts are defined in XML files in the src/agent/prompts/ directory.
"""

from src.agent.utils.prompt_builder import PromptBuilder
from src.agent.utils.xml_parser import XMLPromptParser


class PromptLoader:
    """Load and format prompts from XML files for Claude API.

    This class uses XMLPromptParser to load structured prompts from XML files
    and PromptBuilder to format them into strings for Claude API calls.

    Attributes:
        parser: XMLPromptParser instance
        builder: PromptBuilder instance
        system_data: Parsed system prompt data
        patterns: Parsed command patterns
        currency_config: Parsed currency configuration
        templates: Parsed response templates

    Example:
        >>> loader = PromptLoader()
        >>> system_prompt = loader.get_system_prompt()
        >>> 'subscription_assistant' in system_prompt
        True
    """

    def __init__(self):
        """Initialize the prompt loader with XML parser and builder."""
        self.parser = XMLPromptParser()
        self._load_data()
        self._init_builder()

    def _load_data(self) -> None:
        """Load all data from XML files."""
        self.system_data = self.parser.parse_system_prompt()
        self.patterns = self.parser.parse_command_patterns()
        self.currency_config = self.parser.parse_currency_config()
        self.templates = self.parser.parse_response_templates()
        self.command_template = self.parser.parse_command_prompt_template()

    def _init_builder(self) -> None:
        """Initialize the prompt builder with template data."""
        self.builder = PromptBuilder(self.command_template)

    def get_system_prompt(self) -> str:
        """Get formatted system prompt for Claude API.

        Returns:
            Formatted system prompt string

        Example:
            >>> loader = PromptLoader()
            >>> prompt = loader.get_system_prompt()
            >>> 'subscription_assistant' in prompt
            True
        """
        return self.builder.build_system_prompt(self.system_data, self.currency_config)

    def build_command_prompt(self, user_command: str) -> str:
        """Build command parsing prompt with examples.

        Args:
            user_command: User's natural language command

        Returns:
            Formatted prompt for command parsing

        Example:
            >>> loader = PromptLoader()
            >>> prompt = loader.build_command_prompt("Add Netflix for £10")
            >>> 'Add Netflix for £10' in prompt
            True
        """
        return self.builder.build_command_prompt(user_command, self.patterns)

    def get_response_template(self, template_type: str) -> str:
        """Get response template by type.

        Args:
            template_type: Type of response template (e.g., 'success_create')

        Returns:
            Template format string

        Example:
            >>> loader = PromptLoader()
            >>> template = loader.get_response_template('success_create')
            >>> '{name}' in template
            True
        """
        return self.templates.get(template_type, "")

    def format_response(self, template_type: str, **kwargs: any) -> str:
        """Format a response using a template.

        Args:
            template_type: Type of response template
            **kwargs: Template variables to substitute

        Returns:
            Formatted response string

        Example:
            >>> loader = PromptLoader()
            >>> response = loader.format_response(
            ...     'success_create',
            ...     name='Netflix',
            ...     currency_symbol='£',
            ...     amount='15.99',
            ...     frequency='monthly'
            ... )
            >>> 'Netflix' in response
            True
        """
        template = self.get_response_template(template_type)
        if not template:
            return ""

        try:
            return template.format(**kwargs)
        except KeyError:
            return template
