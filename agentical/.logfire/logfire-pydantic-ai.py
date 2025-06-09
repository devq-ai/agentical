# /// script
# dependencies = ["logfire", "pydantic_ai_slim[openai]"]
# ///

# This example demonstrates PydanticAI running with OpenAI!

from pydantic_ai import Agent
import logfire

# configure logfire
logfire.configure(token='pylf_v1_us_n8M6yFc726WDBR6yNmMlztslCvYPQq2GSHqbdHBF0PJy')
logfire.instrument_openai()

agent = Agent('openai:gpt-4o')

result = await agent.run(
    'How does pyodide let you run Python in the browser? (short answer please)'
)

print(f'output: {result.output}')