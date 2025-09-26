import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

export interface TechNewsArticle {
  title: string;
  source: string;
  publishedAt: string;
  description: string;
  url: string;
}

export class TechNewsMcpService {
  private client: Client | null = null;
  private transport: StdioClientTransport | null = null;
  private isConnected = false;

  constructor(private mcpServerPath: string) {}

  async connect(): Promise<void> {
    if (this.isConnected) {
      return;
    }

    try {
      // Create transport that will spawn the MCP server process
      this.transport = new StdioClientTransport({
        command: 'node',
        args: [this.mcpServerPath],
        stderr: 'inherit',
        env: {
          ...process.env,
          // Add News API key if available from either environment variable name
          NEWS_API_KEY: process.env.NEWS_API_KEY || process.env.SECRET_NEWS_API_KEY || 'YOUR_API_KEY_HERE'
        }
      });

      this.client = new Client(
        {
          name: 'teams-ai-agent-news',
          version: '1.0.0',
        },
        {
          capabilities: {},
        }
      );

      // Connect to the server
      await this.client.connect(this.transport);
      this.isConnected = true;

      console.log('Connected to Tech News MCP Server');

    } catch (error) {
      console.error('Failed to connect to Tech News MCP server:', error);
      this.disconnect();
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (this.client && this.transport) {
      await this.client.close();
    }

    this.client = null;
    this.transport = null;
    this.isConnected = false;
  }

  async getTechNews(category: 'general' | 'ai' | 'startups' | 'cybersecurity' | 'mobile' | 'gaming' = 'general', limit: number = 10): Promise<string> {
    if (!this.client || !this.isConnected) {
      throw new Error('Tech News MCP client not connected');
    }

    try {
      console.log(`Calling MCP server tool 'get_tech_news' with category: ${category}, limit: ${limit}`);
      const result = await this.client.callTool({
        name: 'get_tech_news',
        arguments: { category, limit }
      });

      console.log('MCP server response received for tech news');
      if (result.content && Array.isArray(result.content) && result.content.length > 0) {
        const firstContent = result.content[0] as any;
        const newsText = firstContent.text || 'No tech news available';
        console.log(`Tech news data length: ${newsText.length} characters`);
        return newsText;
      }

      return 'No tech news found';
    } catch (error) {
      console.error('Error getting tech news from MCP server:', error);
      throw new Error(`Failed to get tech news from MCP server: ${error}`);
    }
  }

  async searchTechNews(keyword: string, limit: number = 10, timeframe: 'today' | 'week' | 'month' = 'week'): Promise<string> {
    if (!this.client || !this.isConnected) {
      throw new Error('Tech News MCP client not connected');
    }

    try {
      console.log(`Calling MCP server tool 'search_tech_news' with keyword: ${keyword}, timeframe: ${timeframe}`);
      const result = await this.client.callTool({
        name: 'search_tech_news',
        arguments: { keyword, limit, timeframe }
      });

      console.log('MCP server response received for tech news search');
      if (result.content && Array.isArray(result.content) && result.content.length > 0) {
        const firstContent = result.content[0] as any;
        const searchResults = firstContent.text || 'No search results available';
        console.log(`Tech news search results length: ${searchResults.length} characters`);
        return searchResults;
      }

      return 'No search results found';
    } catch (error) {
      console.error('Error searching tech news from MCP server:', error);
      throw new Error(`Failed to search tech news from MCP server: ${error}`);
    }
  }

  async getTrendingTech(region: 'us' | 'gb' | 'ca' | 'au' = 'us', limit: number = 10): Promise<string> {
    if (!this.client || !this.isConnected) {
      throw new Error('Tech News MCP client not connected');
    }

    try {
      console.log(`Calling MCP server tool 'get_trending_tech' with region: ${region}, limit: ${limit}`);
      const result = await this.client.callTool({
        name: 'get_trending_tech',
        arguments: { region, limit }
      });

      console.log('MCP server response received for trending tech topics');
      if (result.content && Array.isArray(result.content) && result.content.length > 0) {
        const firstContent = result.content[0] as any;
        const trendingNews = firstContent.text || 'No trending topics available';
        console.log(`Trending tech topics data length: ${trendingNews.length} characters`);
        return trendingNews;
      }

      return 'No trending topics found';
    } catch (error) {
      console.error('Error getting trending tech topics from MCP server:', error);
      throw new Error(`Failed to get trending tech topics from MCP server: ${error}`);
    }
  }

  async getCompanyNews(company: string, limit: number = 8, timeframe: 'today' | 'week' | 'month' = 'week'): Promise<string> {
    if (!this.client || !this.isConnected) {
      throw new Error('Tech News MCP client not connected');
    }

    try {
      console.log(`Calling MCP server tool 'get_company_news' with company: ${company}, timeframe: ${timeframe}`);
      const result = await this.client.callTool({
        name: 'get_company_news',
        arguments: { company, limit, timeframe }
      });

      console.log('MCP server response received for company news');
      if (result.content && Array.isArray(result.content) && result.content.length > 0) {
        const firstContent = result.content[0] as any;
        const companyNews = firstContent.text || 'No company news available';
        console.log(`Company news data length: ${companyNews.length} characters`);
        return companyNews;
      }

      return 'No company news found';
    } catch (error) {
      console.error('Error getting company news from MCP server:', error);
      throw new Error(`Failed to get company news from MCP server: ${error}`);
    }
  }

  isServiceConnected(): boolean {
    return this.isConnected;
  }
}