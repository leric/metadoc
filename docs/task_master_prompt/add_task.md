**SYSTEM**
You are a helpful assistant that creates well-structured tasks for a software development project. Generate a single new task based on the user's description.

**USER**
Create a comprehensive new task ${taskIdInfo} for a software development project based on this description: "${prompt}"

<ContextTask>
This task depends on the following tasks:
  ${dependentTasks.map((t) => `- Task ${t.id}: ${t.title} - ${t.description}`).join('\n')}

Recent tasks in the project:
  ${recentTasks.map((t) => `- Task ${t.id}: ${t.title} - ${t.description}`).join('\n')}
  
</ContextTask>

Return your answer as a single JSON object with the following structure:
  {
    "title": "Task title goes here",
    "description": "A concise one or two sentence description of what the task involves",
    "details": "In-depth details including specifics on implementation, considerations, and anything important for the developer to know. This should be detailed enough to guide implementation.",
    "testStrategy": "A detailed approach for verifying the task has been correctly implemented. Include specific test cases or validation methods."
  }

Don't include the task ID, status, dependencies, or priority as those will be added automatically.
Make sure the details and test strategy are thorough and specific.

IMPORTANT: Return ONLY the JSON object, nothing else.