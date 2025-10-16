from agent_framework import ChatAgent  
from agent_framework.openai import OpenAIChatClient  
from agent_framework.devui import serve  
  
agent = ChatAgent(  
    name="WeatherAgent",  
    chat_client=OpenAIChatClient(),  
    tools=[get_weather]  
)  
  
serve(entities=[agent], auto_open=True)  