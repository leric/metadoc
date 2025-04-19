---
name: doctype_def
description: Template and guidelines for creating document type definitions
version: 0.1.0
doctype: doctype
---

# DocType Definition Document Type

This document type is designed for defining document types in the Airic workspace.
Document types define the structure, purpose, and processing rules for different kinds of documents.

## Structure

DocType definition documents should include:

1. **Metadata (YAML Frontmatter):**
   ```yaml
   ---
   name: doctype_name           # Required: Unique identifier for the doctype
   description: Short summary   # Required: Brief description of doctype's purpose
   version: 0.1.0               # Required: Semantic version
   ---
   ```

2. **Purpose Description:**
   - Detailed explanation of what this document type is used for
   - When and why to use this document type

3. **Structure Guidelines:**
   - Required and optional sections
   - Formatting and content requirements
   - Any special syntax or conventions

4. **Examples (Optional):**
   - Sample document snippets showing proper structure
   - Templates that can be copied and adapted

## Guidelines

- Focus on structure more than content requirements
- Provide clear, actionable guidelines for document creation
- Balance flexibility and standardization
- Consider both human readability and machine processability
- Test document types with relevant agents to ensure compatibility
