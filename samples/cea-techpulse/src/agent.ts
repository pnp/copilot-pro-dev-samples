import { ActivityTypes } from "@microsoft/agents-activity";
import { AgentApplication, MemoryStorage, TurnContext } from "@microsoft/agents-hosting";
import { AzureOpenAI, OpenAI } from "openai";
import config from "./config.js";
import { TechNewsMcpService } from "./techNewsMcpService.js";
import path from "path";
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('Initializing agent...');
console.log('OpenAI API Key present:', !!config.openAIKey);
console.log('OpenAI Model:', config.openAIModelName);

if (!config.openAIKey) {
  console.error('OPENAI_API_KEY is missing from environment variables!');
  throw new Error('OPENAI_API_KEY is required');
}

const client = new OpenAI({
  apiKey: config.openAIKey,
});

console.log('OpenAI client initialized successfully');

// Initialize the Tech News MCP Service
const techNewsMcpServerPath = path.join(__dirname, "mcpserver", "tech-news.js");
const techNewsService = new TechNewsMcpService(techNewsMcpServerPath);
console.log('Tech News service initialized with path:', techNewsMcpServerPath);

const systemPrompt = `You are an AI agent that can chat with users and provide tech news. 
You can help users with:
1. Getting tech news from various categories (general tech, AI/ML, startups, cybersecurity, mobile, gaming)
2. Searching for specific tech news topics
3. Getting trending tech stories
4. Finding news about specific companies

When users ask about tech news, determine what type of news they want and any specific topics or companies they're interested in.`;

// Define storage and application
const storage = new MemoryStorage();
export const agentApp = new AgentApplication({
  storage,
});

console.log('Agent application initialized');

// Listen for ANY message to be received. MUST BE AFTER ANY OTHER MESSAGE HANDLERS

// Initialize services when the app starts
agentApp.conversationUpdate("membersAdded", async (context: TurnContext) => {
  console.log('New member added to conversation');
  try {
    console.log('Attempting to connect to tech news service...');
    await techNewsService.connect();
    console.log('Tech news service connected successfully');
    
    await context.sendActivity(`Hi there! I'm an AI agent that can chat with you and provide tech news. I can help you get tech news from various categories, search tech topics, and find company news.`);
  } catch (error) {
    console.error("Failed to connect to services:", error);
    await context.sendActivity(`Hi there! I'm an AI agent, but I'm having trouble connecting to some services right now.`);
  }
});

// Listen for ANY message to be received. MUST BE AFTER ANY OTHER MESSAGE HANDLERS
agentApp.activity(ActivityTypes.Message, async (context: TurnContext) => {
  console.log('Received message:', context.activity.text);
  const userMessage = context.activity.text.toLowerCase();
  
  try {
    // Comprehensive check for ANY news-related request - ALL news should go to MCP server
    if (
      // Direct news keywords
      userMessage.includes('news') ||
      userMessage.includes('headlines') ||
      userMessage.includes('articles') ||
      userMessage.includes('updates') ||
      userMessage.includes('latest') ||
      userMessage.includes('breaking') ||
      userMessage.includes('recent') ||
      
      // Technology keywords
      userMessage.includes('tech') ||
      userMessage.includes('technology') ||
      userMessage.includes('software') ||
      userMessage.includes('hardware') ||
      userMessage.includes('innovation') ||
      
      // Specific tech domains
      userMessage.includes('ai') ||
      userMessage.includes('artificial intelligence') ||
      userMessage.includes('machine learning') ||
      userMessage.includes('ml') ||
      userMessage.includes('startup') ||
      userMessage.includes('startups') ||
      userMessage.includes('venture') ||
      userMessage.includes('cybersecurity') ||
      userMessage.includes('security') ||
      userMessage.includes('privacy') ||
      userMessage.includes('hack') ||
      userMessage.includes('mobile') ||
      userMessage.includes('smartphone') ||
      userMessage.includes('android') ||
      userMessage.includes('ios') ||
      userMessage.includes('gaming') ||
      userMessage.includes('games') ||
      userMessage.includes('esports') ||
      userMessage.includes('nintendo') ||
      userMessage.includes('xbox') ||
      userMessage.includes('playstation') ||
      
      // Company names (major tech companies)
      userMessage.includes('microsoft') ||
      userMessage.includes('apple') ||
      userMessage.includes('google') ||
      userMessage.includes('amazon') ||
      userMessage.includes('meta') ||
      userMessage.includes('facebook') ||
      userMessage.includes('netflix') ||
      userMessage.includes('tesla') ||
      userMessage.includes('openai') ||
      userMessage.includes('nvidia') ||
      userMessage.includes('intel') ||
      userMessage.includes('adobe') ||
      userMessage.includes('salesforce') ||
      userMessage.includes('oracle') ||
      
      // Action words that might relate to news
      userMessage.includes('trending') ||
      userMessage.includes('popular') ||
      userMessage.includes('hot topics') ||
      userMessage.includes('search') ||
      userMessage.includes('find') ||
      userMessage.includes('show me') ||
      userMessage.includes('tell me about') ||
      userMessage.includes('what about') ||
      userMessage.includes('whats happening') ||
      userMessage.includes("what's happening") ||
      userMessage.includes('update me') ||
      userMessage.includes('inform me')
    ) {
      
      console.log('Processing tech news-related message via MCP server');
      
      if (!techNewsService.isServiceConnected()) {
        console.log('Tech news service not connected, establishing connection...');
        await techNewsService.connect();
        console.log('Tech news service connection established');
      }
      
      // Check for trending tech news
      if (userMessage.includes('trending') || userMessage.includes('popular') || userMessage.includes('hot topics')) {
        console.log('Fetching trending tech news...');
        const trendingNews = await techNewsService.getTrendingTech();
        await context.sendActivity(`Trending Tech News:\n\n${trendingNews}`);
        return;
      }
      
      // Check for specific company news
      const companyMatch = userMessage.match(/(?:news about|about|tell me about|update on|what about)\s+(.+?)(?:\s|$)/i) || 
                          userMessage.match(/(.+?)\s+(?:news|updates|headlines)/i);
      if (companyMatch && (
        userMessage.includes('news about') || 
        userMessage.includes('company news') ||
        userMessage.includes('tell me about') ||
        userMessage.includes('update on') ||
        userMessage.includes('what about')
      )) {
        const company = companyMatch[1].trim();
        console.log(`Fetching news for company: ${company}`);
        const companyNews = await techNewsService.getCompanyNews(company);
        await context.sendActivity(`News about ${company}:\n\n${companyNews}`);
        return;
      }
      
      // Check for specific search terms
      if (userMessage.includes('search') || userMessage.includes('find')) {
        const searchMatch = userMessage.match(/(?:search|find)(?:\s+(?:for|about))?\s+(.+)/i);
        if (searchMatch) {
          const searchQuery = searchMatch[1].trim();
          console.log(`Searching tech news for: ${searchQuery}`);
          const searchResults = await techNewsService.searchTechNews(searchQuery);
          await context.sendActivity(`Tech news search results for "${searchQuery}":\n\n${searchResults}`);
          return;
        }
      }
      
      // Determine category based on keywords
      let category: 'general' | 'ai' | 'startups' | 'cybersecurity' | 'mobile' | 'gaming' = 'general';
      if (userMessage.includes('ai') || userMessage.includes('artificial intelligence') || 
          userMessage.includes('machine learning') || userMessage.includes('ml')) {
        category = 'ai';
      } else if (userMessage.includes('startup') || userMessage.includes('startups') || userMessage.includes('venture')) {
        category = 'startups';
      } else if (userMessage.includes('cybersecurity') || userMessage.includes('security') || 
                 userMessage.includes('privacy') || userMessage.includes('hack')) {
        category = 'cybersecurity';
      } else if (userMessage.includes('mobile') || userMessage.includes('smartphone') || 
                 userMessage.includes('android') || userMessage.includes('ios')) {
        category = 'mobile';
      } else if (userMessage.includes('gaming') || userMessage.includes('game') || userMessage.includes('games') ||
                 userMessage.includes('esports') || userMessage.includes('nintendo') ||
                 userMessage.includes('xbox') || userMessage.includes('playstation')) {
        category = 'gaming';
      }
      
      console.log(`Fetching tech news for category: ${category}`);
      const techNews = await techNewsService.getTechNews(category);
      await context.sendActivity(`Tech News (${category}):\n\n${techNews}`);
      return;
    }
    
    // Only use OpenAI for completely non-tech, non-news related general chat
    console.log('Processing general chat message with OpenAI (non-news/non-tech)');
    const result = await client.chat.completions.create({
      messages: [
        {
          role: "system",
          content: systemPrompt,
        },
        {
          role: "user",
          content: context.activity.text,
        },
      ],
      model: config.openAIModelName
    });
    
    let answer = "";
    for (const choice of result.choices) {
      answer += choice.message.content;
    }
    console.log('OpenAI response:', answer);
    await context.sendActivity(answer);
    
  } catch (error) {
    console.error("Error processing message:", error);
    await context.sendActivity("Sorry, I encountered an error while processing your request. Please try again.");
  }
});
