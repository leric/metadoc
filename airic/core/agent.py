import os
import asyncio
from google.adk.agents import LlmAgent
from google.adk.models import GeminiFlash15
from google.adk.runners import Runner
from google.adk.sessions import SessionService, InMemorySessionService, Event
# from google.generativeai.types import Content, Part # We might not need these directly if Runner handles history

# Constants (Consider making these configurable or dynamic)
APP_NAME = "airic_repl"
DEFAULT_USER_ID = "repl_user"

# TODO: Configure model and API key properly (e.g., from environment variables)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable not set. Agent functionality will be limited.")
    # Add fallback logic or raise error if API key is strictly required at init
    # raise ValueError("GEMINI_API_KEY environment variable is required.")

# 1. Define the Agent
# Basic agent configuration - this will likely need refinement
# based on specific project needs and Google ADK setup.
agent = LlmAgent(
    name="MetadocAgent",
    description="Agent to interact with documents and answer questions.",
    # Ensure the model is instantiated correctly, handle potential missing key
    model=GeminiFlash15(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None,
    instruction="You are a helpful assistant interacting with document context.",
    # examples=[],
    # tools=[], # Add tools later as needed
)

# 2. Setup Runner and Session Service
# Use InMemorySessionService for simplicity in REPL context
session_service: SessionService = InMemorySessionService()

# Create the runner instance
runner = Runner(session_service=session_service)


# 3. Define Interaction Function using Runner
async def interact_with_agent(user_input: str, user_id: str = DEFAULT_USER_ID) -> str:
    """
    Interacts with the configured Google ADK agent using the Runner.

    Args:
        user_input: The user's message.
        user_id: The ID of the user interacting.

    Returns:
        The agent's response as a string.
    """
    if not agent.model:
        return "Error: Agent model not configured (GEMINI_API_KEY missing?)"

    try:
        # Run the agent via the runner
        # The runner handles session creation/retrieval and event logging
        response_event: Event = await runner.run_async(
            agent=agent,
            app_name=APP_NAME,
            user_id=user_id,
            input=user_input,
            # session_id can be omitted for runner to manage/create
        )

        # Extract the text response from the last event (typically model response)
        # Check the structure of response_event based on ADK documentation/examples
        # Assuming the last relevant part is the model's text output
        if response_event and response_event.data and response_event.data.parts:
            # Find the first text part
            text_part = next((part.text for part in response_event.data.parts if hasattr(part, 'text')), None)
            if text_part:
                return text_part
            else:
                 # Handle cases where the response might be a tool call or other non-text data
                 # For now, return a placeholder if no simple text is found
                 return f"(Agent responded with non-text data: {response_event.type})"
        else:
            return "Error: Received an empty or unexpected response from the agent."

    except Exception as e:
        # Log the full error for debugging
        # Consider using Python's logging module
        print(f"Error during agent interaction: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc() # Print stack trace for detailed debugging
        return f"Sorry, I encountered an error during processing: {e}"

# --- Removed old run_agent_async function --- #

# Example usage (optional, for testing within this module)
async def _test_interaction():
    print("Testing agent interaction...")
    test_input = "Hello, agent! What can you do?"
    print(f"User: {test_input}")
    response = await interact_with_agent(test_input)
    print(f"Agent: {response}")

if __name__ == "__main__":
    # Note: Requires GEMINI_API_KEY to be set in the environment
    if GEMINI_API_KEY and agent.model:
        print("Running agent test...")
        asyncio.run(_test_interaction())
    else:
        print("Set GEMINI_API_KEY and ensure model is configured to run the test.") 