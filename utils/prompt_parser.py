"""
Prompt Parser - Extracts structured information from natural language prompts.
"""

import re
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse


class PromptParser:
    """
    Parses user prompts to extract structured information.
    
    Extracts:
    - Domain hints (URLs, domains)
    - JSON schema requirements
    - Task type classification
    - Constraint extraction
    """
    
    @staticmethod
    def parse(prompt: str, domains: Optional[str] = None, 
              json_schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse a prompt and extract structured information.
        
        Args:
            prompt: Natural language task description
            domains: Optional domain hints (comma-separated)
            json_schema: Optional JSON schema string
        
        Returns:
            Dictionary with parsed information
        """
        result = {
            "prompt": prompt,
            "domains": PromptParser._extract_domains(prompt, domains),
            "urls": PromptParser._extract_urls(prompt),
            "task_type": PromptParser._classify_task(prompt),
            "json_schema": PromptParser._parse_json_schema(json_schema),
            "constraints": PromptParser._extract_constraints(prompt)
        }
        
        return result
    
    @staticmethod
    def _extract_domains(prompt: str, domain_hints: Optional[str] = None) -> List[str]:
        """Extract domain names from prompt and hints."""
        domains = set()
        
        # Add explicit domain hints
        if domain_hints:
            for domain in domain_hints.split(","):
                domain = domain.strip().lower()
                if domain:
                    domains.add(domain)
        
        # Extract from URLs in prompt
        urls = PromptParser._extract_urls(prompt)
        for url in urls:
            parsed = urlparse(url)
            if parsed.netloc:
                domains.add(parsed.netloc.lower())
        
        # Look for domain-like patterns
        domain_pattern = r'\b([a-zA-Z0-9-]+\.(?:com|org|net|edu|gov|io|co|ai))\b'
        matches = re.findall(domain_pattern, prompt.lower())
        domains.update(matches)
        
        return sorted(list(domains))
    
    @staticmethod
    def _extract_urls(prompt: str) -> List[str]:
        """Extract URLs from prompt."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, prompt)
        return urls
    
    @staticmethod
    def _classify_task(prompt: str) -> str:
        """
        Classify the task type based on keywords.
        
        Returns:
            Task type: "navigation", "data_extraction", "form_filling", "search", "general"
        """
        prompt_lower = prompt.lower()
        
        # Keywords for each task type
        navigation_keywords = ["go to", "navigate", "visit", "open", "browse"]
        extraction_keywords = ["find", "extract", "get", "retrieve", "scrape", "collect"]
        form_keywords = ["fill", "submit", "enter", "input", "type"]
        search_keywords = ["search", "lookup", "query", "find"]
        
        # Count matches
        nav_count = sum(1 for kw in navigation_keywords if kw in prompt_lower)
        extract_count = sum(1 for kw in extraction_keywords if kw in prompt_lower)
        form_count = sum(1 for kw in form_keywords if kw in prompt_lower)
        search_count = sum(1 for kw in search_keywords if kw in prompt_lower)
        
        # Determine primary task type
        max_count = max(nav_count, extract_count, form_count, search_count)
        
        if max_count == 0:
            return "general"
        elif extract_count == max_count:
            return "data_extraction"
        elif form_count == max_count:
            return "form_filling"
        elif search_count == max_count:
            return "search"
        else:
            return "navigation"
    
    @staticmethod
    def _parse_json_schema(json_schema: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse JSON schema string."""
        if not json_schema:
            return None
        
        try:
            return json.loads(json_schema)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def _extract_constraints(prompt: str) -> Dict[str, Any]:
        """
        Extract constraints from the prompt.
        
        Returns:
            Dictionary of constraints (e.g., max_items, time_limit, etc.)
        """
        constraints = {}
        
        # Look for numerical constraints
        top_n_match = re.search(r'top\s+(\d+)', prompt.lower())
        if top_n_match:
            constraints["max_items"] = int(top_n_match.group(1))
        
        first_n_match = re.search(r'first\s+(\d+)', prompt.lower())
        if first_n_match:
            constraints["max_items"] = int(first_n_match.group(1))
        
        # Look for time constraints
        if "quickly" in prompt.lower() or "fast" in prompt.lower():
            constraints["speed_priority"] = True
        
        return constraints

