"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

class Config:
    """Agent Configuration"""

    def __init__(self, env):
        self.PORT = 3978
        self.openai_api_key = env["OPENAI_API_KEY"] # OpenAI API key
        self.openai_model_name = 'gpt-4o' # OpenAI model name. You can use any other model name from OpenAI.
        self.news_api_key = env["NEWS_API_KEY"] # News API key from https://newsapi.org/
