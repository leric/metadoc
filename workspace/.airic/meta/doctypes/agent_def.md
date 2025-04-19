---
name: agent_def
description: Template and guidelines for creating agent definitions
version: 0.1.0
doctype: doctype
---

# Agent Definition Document Type

This document type is designed for defining agents in the Airic workspace. 
Agents are specialized AI assistants that follow specific behavior patterns when interacting with documents.

## Structure

Agent definition documents should include:

1. **Metadata (YAML Frontmatter):**
   ```yaml
   ---
   name: agent_name              # Required: Unique identifier for the agent
   description: Short summary    # Required: Brief description of agent's purpose
   version: 0.1.0                # Required: Semantic version
   tools: [tool1, tool2]         # Optional: Tools this agent can use (future feature)
   ---
   ```

2. **Agent Description:**
   - Detailed explanation of the agent's purpose and capabilities
   - Target use cases and document types it works best with

3. **System Prompt:**
   - Specific instructions that define the agent's behavior
   - Personality traits, response style, and expertise areas
   - Constraints and guidelines for interactions

4. **Examples (Optional):**
   - Sample interactions showing how the agent should respond
   - "Do" and "Don't" examples to clarify behavior boundaries

## Guidelines

- Keep system prompts specific and focused on a single responsibility
- Use clear, direct language in system prompts
- Avoid contradictory instructions
- Consider the agent's limitations when defining capabilities
- Test agents with various document types and user queries
