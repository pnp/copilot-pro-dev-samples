import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const NEWS_API_BASE = "https://newsapi.org/v2";
// You'll need to get a free API key from https://newsapi.org/
const NEWS_API_KEY = process.env.NEWS_API_KEY || process.env.SECRET_NEWS_API_KEY || "DEMO_KEY";
const USER_AGENT = "tech-news-mcp-server/1.0";

console.log('Tech News MCP Server - API Key status:', NEWS_API_KEY !== "DEMO_KEY" ? 'Available' : 'Demo mode (get key from newsapi.org)');

// Create server instance
const server = new McpServer({
    name: "tech-news",
    version: "1.0.0",
    capabilities: {
        resources: {},
        tools: {},
    },
});

// Helper function for making News API requests
async function makeNewsAPIRequest(endpoint, params = {}) {
    // Check if API key is available
    if (NEWS_API_KEY === " ") {
        throw new Error("News API key is required. Get your free API key from https://newsapi.org/");
    }

    const url = new URL(`${NEWS_API_BASE}/${endpoint}`);
    
    // Add API key and default parameters
    url.searchParams.set('apiKey', NEWS_API_KEY);
    
    // Add additional parameters
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            url.searchParams.set(key, value.toString());
        }
    });

    const headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    };

    try {
        const response = await fetch(url.toString(), { headers });
        if (!response.ok) {
            throw new Error(`News API error: ${response.status} - ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Error making News API request:", error);
        throw error;
    }
}

// Format news article
function formatArticle(article, index) {
    const publishedDate = new Date(article.publishedAt).toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    return [
        `${index}. ${article.title}`,
        `Source: ${article.source.name}`,
        `Published: ${publishedDate}`,
        `Description: ${article.description || 'No description available'}`,
        `URL: ${article.url}`,
        "---"
    ].join("\n");
}

// Register tool: Get latest tech news
server.tool("get_tech_news", "Get latest technology news headlines", {
    category: z.enum(['general', 'ai', 'startups', 'cybersecurity', 'mobile', 'gaming']).optional().describe("Specific tech category (default: general)"),
    limit: z.number().min(1).max(20).optional().describe("Number of articles to return (1-20, default: 10)"),
    country: z.string().length(2).optional().describe("Country code for news (e.g., 'us', 'gb', default: 'us')")
}, async ({ category = 'general', limit = 10, country = 'us' }) => {
    try {
        // Define tech-related queries based on category
        const techQueries = {
            'general': 'technology OR tech OR software OR hardware OR startup',
            'ai': 'artificial intelligence OR machine learning OR AI OR ChatGPT OR OpenAI',
            'startups': 'startup OR venture capital OR funding OR IPO OR tech company',
            'cybersecurity': 'cybersecurity OR hacking OR data breach OR security OR malware',
            'mobile': 'smartphone OR iPhone OR Android OR mobile app OR tablet',
            'gaming': 'gaming OR video games OR esports OR PlayStation OR Xbox OR Nintendo'
        };

        const query = techQueries[category] || techQueries['general'];

        const newsData = await makeNewsAPIRequest('everything', {
            q: query,
            language: 'en',
            sortBy: 'publishedAt',
            pageSize: limit,
            domains: 'techcrunch.com,theverge.com,arstechnica.com,wired.com,engadget.com,venturebeat.com,zdnet.com,cnet.com,recode.net,mashable.com'
        });

        if (!newsData || !newsData.articles) {
            return {
                content: [{
                    type: "text",
                    text: "Failed to retrieve tech news data",
                }],
            };
        }

        const articles = newsData.articles || [];
        if (articles.length === 0) {
            return {
                content: [{
                    type: "text",
                    text: `No tech news found for category: ${category}`,
                }],
            };
        }

        const formattedArticles = articles.slice(0, limit).map((article, index) => 
            formatArticle(article, index + 1)
        );

        const newsText = `Latest Tech News - ${category.toUpperCase()} (${articles.length} articles):\n\n${formattedArticles.join("\n")}`;

        return {
            content: [{
                type: "text",
                text: newsText,
            }],
        };
    } catch (error) {
        console.error("Error getting tech news:", error);
        return {
            content: [{
                type: "text",
                text: `Failed to get tech news: ${error.message}`,
            }],
        };
    }
});

// Register tool: Search tech news by keyword
server.tool("search_tech_news", "Search for specific tech news by keyword", {
    keyword: z.string().min(1).describe("Keyword to search for in tech news"),
    limit: z.number().min(1).max(20).optional().describe("Number of articles to return (1-20, default: 10)"),
    timeframe: z.enum(['today', 'week', 'month']).optional().describe("Time range for news (default: week)")
}, async ({ keyword, limit = 10, timeframe = 'week' }) => {
    try {
        // Calculate date range based on timeframe
        const now = new Date();
        const fromDate = new Date();
        
        switch (timeframe) {
            case 'today':
                fromDate.setDate(now.getDate() - 1);
                break;
            case 'week':
                fromDate.setDate(now.getDate() - 7);
                break;
            case 'month':
                fromDate.setMonth(now.getMonth() - 1);
                break;
        }

        // Enhance search with tech-related terms
        const enhancedQuery = `(${keyword}) AND (technology OR tech OR software OR startup OR AI OR cybersecurity)`;

        const newsData = await makeNewsAPIRequest('everything', {
            q: enhancedQuery,
            language: 'en',
            sortBy: 'relevancy',
            pageSize: limit,
            from: fromDate.toISOString().split('T')[0],
            to: now.toISOString().split('T')[0],
            domains: 'techcrunch.com,theverge.com,arstechnica.com,wired.com,engadget.com,venturebeat.com,zdnet.com,cnet.com,recode.net,mashable.com,reuters.com,bloomberg.com'
        });

        if (!newsData || !newsData.articles) {
            return {
                content: [{
                    type: "text",
                    text: `Failed to search tech news for: ${keyword}`,
                }],
            };
        }

        const articles = newsData.articles || [];
        if (articles.length === 0) {
            return {
                content: [{
                    type: "text",
                    text: `No tech news found for keyword: ${keyword} in timeframe: ${timeframe}`,
                }],
            };
        }

        const formattedArticles = articles.slice(0, limit).map((article, index) => 
            formatArticle(article, index + 1)
        );

        const newsText = `Tech News Search Results for "${keyword}" (${timeframe}):\nFound ${articles.length} articles\n\n${formattedArticles.join("\n")}`;

        return {
            content: [{
                type: "text",
                text: newsText,
            }],
        };
    } catch (error) {
        console.error("Error searching tech news:", error);
        return {
            content: [{
                type: "text",
                text: `Failed to search tech news: ${error.message}`,
            }],
        };
    }
});

// Register tool: Get trending tech topics
server.tool("get_trending_tech", "Get trending technology topics and headlines", {
    region: z.enum(['us', 'gb', 'ca', 'au']).optional().describe("Region for trending topics (default: us)"),
    limit: z.number().min(1).max(15).optional().describe("Number of trending articles to return (1-15, default: 10)")
}, async ({ region = 'us', limit = 10 }) => {
    try {
        const newsData = await makeNewsAPIRequest('top-headlines', {
            category: 'technology',
            country: region,
            pageSize: limit
        });

        if (!newsData || !newsData.articles) {
            return {
                content: [{
                    type: "text",
                    text: "Failed to retrieve trending tech topics",
                }],
            };
        }

        const articles = newsData.articles || [];
        if (articles.length === 0) {
            return {
                content: [{
                    type: "text",
                    text: `No trending tech topics found for region: ${region}`,
                }],
            };
        }

        const formattedArticles = articles.slice(0, limit).map((article, index) => 
            formatArticle(article, index + 1)
        );

        const trendingText = `Trending Tech Topics (${region.toUpperCase()}) - ${articles.length} articles:\n\n${formattedArticles.join("\n")}`;

        return {
            content: [{
                type: "text",
                text: trendingText,
            }],
        };
    } catch (error) {
        console.error("Error getting trending tech topics:", error);
        return {
            content: [{
                type: "text",
                text: `Failed to get trending tech topics: ${error.message}`,
            }],
        };
    }
});

// Register tool: Get tech company news
server.tool("get_company_news", "Get news about specific tech companies", {
    company: z.string().min(1).describe("Company name (e.g., 'Microsoft', 'Apple', 'Google')"),
    limit: z.number().min(1).max(15).optional().describe("Number of articles to return (1-15, default: 8)"),
    timeframe: z.enum(['today', 'week', 'month']).optional().describe("Time range for news (default: week)")
}, async ({ company, limit = 8, timeframe = 'week' }) => {
    try {
        // Calculate date range
        const now = new Date();
        const fromDate = new Date();
        
        switch (timeframe) {
            case 'today':
                fromDate.setDate(now.getDate() - 1);
                break;
            case 'week':
                fromDate.setDate(now.getDate() - 7);
                break;
            case 'month':
                fromDate.setMonth(now.getMonth() - 1);
                break;
        }

        const newsData = await makeNewsAPIRequest('everything', {
            q: `"${company}"`,
            language: 'en',
            sortBy: 'relevancy',
            pageSize: limit,
            from: fromDate.toISOString().split('T')[0],
            domains: 'techcrunch.com,theverge.com,arstechnica.com,wired.com,engadget.com,venturebeat.com,zdnet.com,cnet.com,bloomberg.com,reuters.com,cnbc.com'
        });

        if (!newsData || !newsData.articles) {
            return {
                content: [{
                    type: "text",
                    text: `Failed to retrieve news for company: ${company}`,
                }],
            };
        }

        const articles = newsData.articles || [];
        if (articles.length === 0) {
            return {
                content: [{
                    type: "text",
                    text: `No recent news found for company: ${company} in timeframe: ${timeframe}`,
                }],
            };
        }

        const formattedArticles = articles.slice(0, limit).map((article, index) => 
            formatArticle(article, index + 1)
        );

        const companyNewsText = `${company} News (${timeframe}) - ${articles.length} articles:\n\n${formattedArticles.join("\n")}`;

        return {
            content: [{
                type: "text",
                text: companyNewsText,
            }],
        };
    } catch (error) {
        console.error("Error getting company news:", error);
        return {
            content: [{
                type: "text",
                text: `Failed to get company news: ${error.message}`,
            }],
        };
    }
});

// Start server
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("Tech News MCP Server running on stdio");
}

main().catch((error) => {
    console.error("Fatal error in main():", error);
    process.exit(1);
});