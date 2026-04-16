import litellm
import json
from tools.retriever import retrieve
from config import OPENROUTER_API_KEY

def run_agent(query: str):
    tools = [{
        "type": "function",
        "function": {
            "name": "retrieve",
            "description": "Always use the retrieval tool to answer strictly from retrieved context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }]
    
    messages = [
        {"role": "system", "content": "You are an ecommerce assistant.\n- Always use the retrieval tool\n- Answer strictly from retrieved context\n- If not found, say 'I couldn't find that information'"},
        {"role": "user", "content": query}
    ]
    
    # Step 1: Call LLM
    response = litellm.completion(
        model="openrouter/openai/gpt-4o-mini",
        api_key=OPENROUTER_API_KEY,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    
    # Step 2: Handle tool calls
    if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
        messages.append(response_message.model_dump()) # Append assistant message with tool calls
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "retrieve":
                args = json.loads(tool_call.function.arguments)
                retrieved_context = retrieve(args["query"])
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": retrieved_context
                })
        
        # Step 3: Call LLM again with tool results
        final_response = litellm.completion(
            model="openrouter/openai/gpt-4o-mini",
            api_key=OPENROUTER_API_KEY,
            messages=messages
        )
        return final_response.choices[0].message.content
        
    return response_message.content

class Agent:
    def run(self, query):
        return run_agent(query)
        
agent = Agent()
