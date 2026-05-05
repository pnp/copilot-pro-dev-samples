import os
import re
from pathlib import Path
from dotenv import load_dotenv

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
)
from microsoft_agents.activity import (
    load_configuration_from_env,
    ActivityTypes,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager
from openai import OpenAI

from config import Config
from tech_news_mcp_service import TechNewsMcpService

load_dotenv()

# Load configuration
config = Config(os.environ)
agents_sdk_config = load_configuration_from_env(os.environ)

client = OpenAI(
    api_key=config.openai_api_key,
)

# Initialize the Tech News MCP Service
tech_news_server_path = str(Path(__file__).parent / "mcpserver" / "tech_news.py")
tech_news_service = TechNewsMcpService(tech_news_server_path)

system_prompt = """You are an AI agent that can chat with users and provide tech news. 
You can help users with:
1. Getting tech news from various categories (general tech, AI/ML, startups, cybersecurity, mobile, gaming)
2. Searching for specific tech news topics
3. Getting trending tech stories
4. Finding news about specific companies

When users ask about tech news, determine what type of news they want and any specific topics or companies they're interested in."""

# Define storage and application
storage = MemoryStorage()
connection_manager = MsalConnectionManager(**agents_sdk_config)
adapter = CloudAdapter(connection_manager=connection_manager)

agent_app = AgentApplication[TurnState](
    storage=storage, 
    adapter=adapter, 
    **agents_sdk_config
)



_NEWS_KEYWORDS = frozenset([
    "news", "headlines", "articles", "updates", "latest", "breaking", "recent",
])

_TECH_KEYWORDS = frozenset([
    "tech", "technology", "software", "hardware", "innovation",
])

_DOMAIN_KEYWORDS = frozenset([
    "ai", "artificial intelligence", "machine learning", "ml",
    "startup", "startups", "venture",
    "cybersecurity", "security", "privacy", "hack",
    "mobile", "smartphone", "android", "ios",
    "gaming", "games", "esports", "nintendo", "xbox", "playstation",
])

_COMPANY_KEYWORDS = frozenset([
    "microsoft", "apple", "google", "amazon", "meta", "facebook",
    "netflix", "tesla", "openai", "nvidia", "intel", "adobe",
    "salesforce", "oracle",
])

_ACTION_KEYWORDS = frozenset([
    "trending", "popular", "hot topics",
    "search", "find", "show me", "tell me about", "what about",
    "whats happening", "what's happening", "update me", "inform me",
])

_ALL_TRIGGER_KEYWORDS = (
    _NEWS_KEYWORDS | _TECH_KEYWORDS | _DOMAIN_KEYWORDS | _COMPANY_KEYWORDS | _ACTION_KEYWORDS
)


def _is_news_related(text: str) -> bool:
    """Return True if the message looks like a tech-news request."""
    return any(kw in text for kw in _ALL_TRIGGER_KEYWORDS)


def _detect_category(text: str) -> str:
    if any(kw in text for kw in ("ai", "artificial intelligence", "machine learning", "ml")):
        return "ai"
    if any(kw in text for kw in ("startup", "startups", "venture")):
        return "startups"
    if any(kw in text for kw in ("cybersecurity", "security", "privacy", "hack")):
        return "cybersecurity"
    if any(kw in text for kw in ("mobile", "smartphone", "android", "ios")):
        return "mobile"
    if any(kw in text for kw in ("gaming", "game", "games", "esports", "nintendo", "xbox", "playstation")):
        return "gaming"
    return "general"


@agent_app.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    try:
        await tech_news_service.connect()
        await context.send_activity(
            "Hi there! I'm an AI agent that can chat with you and provide tech news. "
            "I can help you get tech news from various categories, search tech topics, "
            "and find company news."
        )
    except Exception as exc:
        await context.send_activity(
            "Hi there! I'm an AI agent, but I'm having trouble connecting to some services right now."
        )


@agent_app.activity(ActivityTypes.message)
async def on_message(context: TurnContext, _state: TurnState):
    user_message = (context.activity.text or "").lower()

    try:
        if _is_news_related(user_message):
            if not tech_news_service.is_service_connected():
                await tech_news_service.connect()

            # Trending
            if any(kw in user_message for kw in ("trending", "popular", "hot topics")):
                result = await tech_news_service.get_trending_tech()
                await context.send_activity(f"Trending Tech News:\n\n{result}")
                return

            # Company news
            company_match = (
                re.search(r"(?:news about|about|tell me about|update on|what about)\s+(.+?)(?:\s|$)", user_message, re.I)
                or re.search(r"(.+?)\s+(?:news|updates|headlines)", user_message, re.I)
            )
            if company_match:
                company = company_match.group(1).strip()
                result = await tech_news_service.get_company_news(company)
                await context.send_activity(f"News about {company}:\n\n{result}")
                return

            # Search
            if any(kw in user_message for kw in ("search", "find")):
                search_match = re.search(r"(?:search|find)(?:\s+(?:for|about))?\s+(.+)", user_message, re.I)
                if search_match:
                    query = search_match.group(1).strip()
                    result = await tech_news_service.search_tech_news(query)
                    await context.send_activity(f'Tech news search results for "{query}":\n\n{result}')
                    return

            # Category-based news
            category = _detect_category(user_message)
            result = await tech_news_service.get_tech_news(category)
            await context.send_activity(f"Tech News ({category}):\n\n{result}")
            return

        # General chat via OpenAI
        result = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context.activity.text},
            ],
            model=config.openai_model_name,
        )

        answer = "".join(choice.message.content or "" for choice in result.choices)
        await context.send_activity(answer)

    except Exception as exc:
        await context.send_activity(
            "Sorry, I encountered an error while processing your request. Please try again."
        )


@agent_app.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    # Send a message to the user
    await context.send_activity("The agent encountered an error or bug.")
