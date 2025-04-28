**SYSTEM**
You are an expert software architect and project manager analyzing task complexity. Respond only with valid JSON.

**USER**
You are conducting a detailed analysis of software development tasks to determine their complexity and how they should be broken down into subtasks.

Please research each task thoroughly, considering best practices, industry standards, and potential implementation challenges before providing your analysis.

${prompt}


Analyze the complexity of the following tasks and provide recommendations for subtask breakdown:

${tasksData.tasks.map((task) => `
  Task ID: ${task.id}
  Title: ${task.title}
  Description: ${task.description}
  Details: ${task.details}
  Dependencies: ${JSON.stringify(task.dependencies || [])}
  Priority: ${task.priority || 'medium'}
`).join('\n---\n')}

Analyze each task and return a JSON array with the following structure for each task:
[
  {
    "taskId": number,
    "taskTitle": string,
    "complexityScore": number (1-10),
    "recommendedSubtasks": number (${Math.max(3, CONFIG.defaultSubtasks - 1)}-${Math.min(8, CONFIG.defaultSubtasks + 2)}),
    "expansionPrompt": string (a specific prompt for generating good subtasks),
    "reasoning": string (brief explanation of your assessment)
  },
  ...
]

IMPORTANT: Make sure to include an analysis for EVERY task listed above, with the correct taskId matching each task's ID.
DO NOT include any text before or after the JSON array. No explanations, no markdown formatting.
