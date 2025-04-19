---
name: workflow_def
description: Template and guidelines for creating workflow definitions
version: 0.1.0
doctype: doctype
---

# Workflow Definition Document Type

This document type is designed for defining workflows in the Airic workspace.
Workflows define multi-step processes that guide users through completing complex tasks.

## Structure

Workflow definition documents should include:

1. **Metadata (YAML Frontmatter):**
   ```yaml
   ---
   name: workflow_name          # Required: Unique identifier for the workflow
   description: Short summary   # Required: Brief description of workflow's purpose
   version: 0.1.0               # Required: Semantic version
   doctype: workflow            # Required: Always set to "workflow"
   ---
   ```

2. **Purpose Description:**
   - Detailed explanation of what this workflow accomplishes
   - When and why to use this workflow

3. **Stages:**
   - Clearly defined steps in the workflow
   - Dependencies between steps
   - Expected inputs and outputs for each step

4. **Usage Instructions:**
   - How to initiate and progress through the workflow
   - How to track status and completion

## Guidelines

- Break complex processes into clear, manageable steps
- Define success criteria for each step and the overall workflow
- Provide guidance for handling common issues or exceptions
- Consider different skill levels when designing workflow instructions
- Test workflows end-to-end to ensure they lead to successful outcomes
