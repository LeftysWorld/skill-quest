from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI


openai_model = ChatOpenAI(
    model="gpt-5-nano",
    timeout=120,
    max_retries=2,
)

claude_model = ChatAnthropic(
    model="claude-sonnet-4-6",
    default_request_timeout=120,
    max_retries=2,
)

robust_model = openai_model.with_fallbacks(
    [claude_model],
    exceptions_to_handle=(Exception,),
)
