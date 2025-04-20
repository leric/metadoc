import os
import asyncio
import logging
from google.adk.agents import LlmAgent
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService, InMemorySessionService
from google.genai.types import Content, Part

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants (Consider making these configurable or dynamic)
APP_NAME = "airic_repl"
DEFAULT_USER_ID = "repl_user"
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1

# TODO: Configure model and API key properly (e.g., from environment variables)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logging.warning("Warning: OPENAI_API_KEY environment variable not set. Agent functionality will be limited.")
    # Add fallback logic or raise error if API key is strictly required at init
    # raise ValueError("GEMINI_API_KEY environment variable is required.")

class ADKAgentProvider:
    """Provides a configured LlmAgent instance."""
    _agent_instance: LlmAgent | None = None

    @classmethod
    def get_agent(cls) -> LlmAgent | None:
        """Gets the singleton LlmAgent instance."""
        if cls._agent_instance is None:
            if OPENAI_API_KEY:
                cls._agent_instance = LlmAgent(
                    name="MetadocAgent",
                    description="Agent to interact with documents and answer questions.",
                    # Ensure the model is instantiated correctly, handle potential missing key
                    model=LiteLlm(model="gpt-4o-mini") if OPENAI_API_KEY else None,
                    instruction="You are a helpful assistant interacting with document context.",
                    # examples=[],
                    # tools=[], # Add tools later as needed
                )
                logging.info("LlmAgent initialized successfully.")
            else:
                logging.error("Cannot initialize LlmAgent: GEMINI_API_KEY is not set.")
        return cls._agent_instance

class AgentInteractor:
    """Handles interaction with the ADK Agent using a Runner."""

    def __init__(self, session_id: str, session_service: BaseSessionService = None):
        self._agent = ADKAgentProvider.get_agent()
        self._session_service = session_service or InMemorySessionService()
        self._runner = Runner(session_service=self._session_service, app_name=APP_NAME, agent=self._agent)
        if not self._agent:
            logging.error("AgentInteractor initialized without a valid agent.")
        self._session_id = session_id
        self._session = None

    async def run_interaction(self, user_input: str, user_id: str = DEFAULT_USER_ID, context: str | None = None) -> str:
        """
        Interacts with the configured Google ADK agent, including retry logic and optional context.

        Args:
            user_input: The user's message.
            user_id: The ID of the user interacting.
            context: Optional context string (e.g., document snippets) to provide to the agent.

        Returns:
            The agent's response as a string, or an error message.
        """
        if not self._agent:
            return "Error: Agent model not configured (GEMINI_API_KEY missing?)"

        if not self._session:
            self._session = self._session_service.get_session(app_name=APP_NAME, session_id=self._session_id, user_id=user_id)
            if not self._session:
                self._session = self._session_service.create_session(app_name=APP_NAME, session_id=self._session_id, user_id=user_id)

        # Format the input with context if provided
        if context:
            full_input = f"Context:\n---\n{context}\n---\n\nUser Query: {user_input}"
            logging.info(f"Running interaction with context (first 100 chars): {context[:100]}...")
        else:
            full_input = user_input
            logging.info("Running interaction without context.")

        retries = 0
        while retries <= MAX_RETRIES:
            try:
                logging.info(f"Running agent interaction (Attempt {retries + 1}/{MAX_RETRIES + 1})")
                input_content = Content(parts=[Part(text=full_input)])
                response_event: Event | None = None
                async for event in self._runner.run_async(
                    session_id=self._session_id,
                    user_id=user_id,
                    new_message=input_content,
                ):
                    if event.is_final_response:
                        response_event = event
                        break

                # Extract the text response
                if response_event and response_event.content and response_event.content.parts:
                    text_part = next((part.text for part in response_event.content.parts if hasattr(part, 'text')), None)
                    if text_part:
                        logging.info("Successfully received text response from agent.")
                        return text_part
                    else:
                        # Handle non-text responses if necessary
                        logging.warning(f"Agent responded with non-text data: {response_event.type}")
                        return f"(Agent responded with non-text data: {response_event.type})"
                else:
                    logging.error("Received an empty or unexpected response structure from the agent.")
                    return "Error: Received an empty or unexpected response from the agent."

            except Exception as e:
                logging.error(f"Error during agent interaction (Attempt {retries + 1}): {type(e).__name__} - {e}", exc_info=True)
                retries += 1
                if retries > MAX_RETRIES:
                    logging.error("Max retries exceeded.")
                    return f"Sorry, I encountered an error after multiple retries: {e}"

                backoff_time = INITIAL_BACKOFF_SECONDS * (2 ** (retries - 1))
                logging.info(f"Retrying in {backoff_time:.2f} seconds...")
                await asyncio.sleep(backoff_time)

        # This part should ideally not be reached if logic is correct
        return "Error: Interaction failed after exhausting retries."

# Example usage (optional, for testing within this module)
async def _test_interaction():
    logging.info("Testing agent interaction...")
    agent_interactor = AgentInteractor() # Uses default InMemorySessionService
    if not agent_interactor._agent:
         logging.warning("Cannot run test: Agent not initialized.")
         return

    test_input = "Hello, agent! What can you do based on the context provided?"
    test_context = "This is some sample document context. It contains information about apples and oranges. Apples are red or green, and oranges are orange."
    logging.info(f"User: {test_input}")
    logging.info(f"Context: {test_context}")
    response = await agent_interactor.run_interaction(test_input, context=test_context)
    logging.info(f"Agent: {response}")

if __name__ == "__main__":
    # Note: Requires GEMINI_API_KEY to be set in the environment
    if ADKAgentProvider.get_agent(): # Check if agent can be initialized
        logging.info("Running agent test...")
        asyncio.run(_test_interaction())
    else:
        logging.warning("Set GEMINI_API_KEY and ensure model is configured to run the test.") 