import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { Toaster } from '@/components/ui/toaster';
import ReactMarkdown from 'react-markdown';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { ChevronDown } from "lucide-react";
import { debounce } from 'lodash';
import { formatMarkdownContent } from '@/utils/markdown';
import { CryptoSelect } from '@/components/CryptoSelect';
import { buildUrl } from '@/config/endpoints';

interface MarketData {
  price: number;
  change24h: number;
  volume: number;
  marketcap: number;
}

interface AgentAnalysis {
  title: string;
  content: string;
  loading: boolean;
}

interface Cryptocurrency {
  id: string;
  symbol: string;
  name: string;
  rank: number;
  platform?: string;
}

const AnalysisPage = () => {
  const { toast } = useToast();
  const [cryptocurrencies, setCryptocurrencies] = useState<Cryptocurrency[]>([]);
  const [selectedCrypto, setSelectedCrypto] = useState<string>("BTC");
  const [marketData, setMarketData] = useState<MarketData>({
    price: 0,
    change24h: 0,
    volume: 0,
    marketcap: 0,
  });
  const [agents, setAgents] = useState<AgentAnalysis[]>([
    { title: 'Market Data Agent', content: 'BTC price trend analysis shows consolidation phase...', loading: false },
    { title: 'Sentiment Agent', content: 'Market sentiment is cautious, social media discussion volume is moderate...', loading: false },
    { title: 'Technical Agent', content: 'RSI indicates oversold conditions, MACD approaching golden cross...', loading: false },
    { title: 'Risk Agent', content: 'Current market volatility is high, position control recommended...', loading: false },
    { title: 'Portfolio Agent', content: 'Recommended position size is 30%, waiting for better entry points...', loading: false },
  ]);
  const [loading, setLoading] = useState(false);
  const [selectedAIProvider, setSelectedAIProvider] = useState<string>("openai");
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const aiProviders = [
    { id: 'openai', name: 'OpenAI' },
    { id: 'anthropic', name: 'Anthropic' }
  ];

  const fetchCryptocurrencies = async () => {
    try {
      const response = await fetch(buildUrl('cryptocurrencies'));
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      const formattedData: Cryptocurrency[] = Array.isArray(data.data) 
        ? data.data.map((crypto: any) => ({
            id: crypto.symbol,
            symbol: crypto.symbol,
            name: crypto.name,
            rank: crypto.rank,
            platform: crypto.platform
          }))
        : [];
      setCryptocurrencies(formattedData);
    } catch (error) {
      console.error('Error fetching cryptocurrencies:', error);
      toast({
        title: "Error",
        description: "Failed to fetch cryptocurrency list. Please try again later.",
        variant: "destructive",
      });
      setCryptocurrencies([]);
    }
  };

  useEffect(() => {
    fetchCryptocurrencies();
  }, []);

  // Separate data fetching logic
  const fetchData = async () => {
    setLoading(true);
    
    // Fetch market data first
    try {
      const marketResponse = await fetch(buildUrl('marketData', selectedCrypto), {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      if (!marketResponse.ok) {
        throw new Error('Market data fetch failed');
      }

      const marketData = await marketResponse.json();
      setMarketData(marketData); // Update market data immediately

      // Then fetch analysis data
      const analysisResponse = await fetch(
        `${buildUrl('analysis', selectedCrypto)}?provider=${selectedAIProvider}`,
        {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (!analysisResponse.ok) {
        throw new Error('Analysis data fetch failed');
      }

      const analysisData = await analysisResponse.json();
      setAgents(analysisData.agents);

    } catch (error) {
      console.error('Fetch error:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Create stable debounced function with latest values
  const debouncedRefresh = useMemo(
    () => debounce(async () => {
      await fetchData();
    }, 500),
    [selectedCrypto, selectedAIProvider] // Add dependencies here
  );

  // Trigger data fetch when dependencies change
  useEffect(() => {
    debouncedRefresh();
    return () => debouncedRefresh.cancel();
  }, [debouncedRefresh]); // Only depend on debouncedRefresh

  const handleCollapsibleChange = (isOpen: boolean, index: number) => {
    setOpenIndex(isOpen ? index : null);
    
    if (isOpen) {
      // Small timeout to ensure the content is rendered before scrolling
      setTimeout(() => {
        const element = document.getElementById(`agent-${index}`);
        element?.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'
        });
      }, 100);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">{selectedCrypto} Market Analysis</h1>
        <div className="flex items-center gap-4">
          <CryptoSelect
            cryptocurrencies={cryptocurrencies}
            value={selectedCrypto}
            onChange={setSelectedCrypto}
            disabled={loading || cryptocurrencies.length === 0}
          />
          
          <Select value={selectedAIProvider} onValueChange={setSelectedAIProvider} disabled={loading}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select AI Provider" />
            </SelectTrigger>
            <SelectContent>
              {aiProviders.map((provider) => (
                <SelectItem key={provider.id} value={provider.id}>
                  {provider.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button onClick={debouncedRefresh} disabled={loading}>
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Refresh Data
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Market Data</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-4 gap-8">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Price</p>
              <p className="text-2xl font-bold">${marketData.price.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">24h Change</p>
              <p className={`text-2xl font-bold ${marketData.change24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {marketData.change24h.toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Volume</p>
              <p className="text-2xl font-bold">
                ${(marketData.volume / 1_000_000_000).toFixed(2)}B
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Market Cap</p>
              <p className="text-2xl font-bold">
                ${(marketData.marketcap / 1_000_000_000).toFixed(2)}B
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h2 className="text-2xl font-bold">AI Agent Analysis</h2>
        {agents.map((agent, index) => (
          <Collapsible 
            key={index}
            open={openIndex === index}
            onOpenChange={(isOpen) => handleCollapsibleChange(isOpen, index)}
          >
            <Card 
              id={`agent-${index}`}
              className="transition-all duration-200 hover:shadow-md hover:bg-muted/20"
            >
              <CollapsibleTrigger className="w-full">
                <CardHeader className="border-b bg-muted/40 flex flex-row items-center justify-between hover:bg-muted/60 transition-colors duration-200">
                  <CardTitle className="text-xl">{agent.title}</CardTitle>
                  <ChevronDown className="h-4 w-4 transition-transform duration-200 collapsible-open:rotate-180" />
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent className="pt-4">
                  <ReactMarkdown 
                    className="prose dark:prose-invert max-w-none"
                    components={{
                      h3: ({children}) => (
                        <h3 className="text-xl font-bold mt-8 mb-4 text-primary border-b pb-2">{children}</h3>
                      ),
                      h4: ({children}) => (
                        <h4 className="text-lg font-semibold mt-6 mb-3 text-foreground">{children}</h4>
                      ),
                      
                      ul: ({children}) => (
                        <ul className="list-disc pl-6 space-y-2 my-4">{children}</ul>
                      ),
                      ol: ({children}) => (
                        <ol className="list-decimal pl-6 space-y-2 my-4">{children}</ol>
                      ),
                      li: ({children}) => (
                        <li className="text-muted-foreground leading-relaxed">{children}</li>
                      ),
                      
                      p: ({children}) => (
                        <p className="text-muted-foreground leading-relaxed mb-4">{children}</p>
                      ),
                      strong: ({children}) => (
                        <strong className="font-bold text-foreground">{children}</strong>
                      ),
                      em: ({children}) => (
                        <em className="text-primary/80 not-italic font-medium">{children}</em>
                      ),
                      
                      hr: () => (
                        <hr className="my-8 border-border/40" />
                      ),
                      
                      blockquote: ({children}) => (
                        <blockquote className="border-l-4 border-primary pl-4 my-4 italic text-muted-foreground">
                          {children}
                        </blockquote>
                      ),
                      
                      table: ({children}) => (
                        <div className="overflow-x-auto my-6">
                          <table className="min-w-full divide-y divide-border">
                            {children}
                          </table>
                        </div>
                      ),
                      th: ({children}) => (
                        <th className="px-4 py-3 text-left text-sm font-semibold text-foreground bg-muted">
                          {children}
                        </th>
                      ),
                      td: ({children}) => (
                        <td className="px-4 py-2 text-sm text-muted-foreground">
                          {children}
                        </td>
                      ),
                      
                      code: ({children}) => (
                        <code className="px-1.5 py-0.5 rounded-md bg-muted text-primary font-mono text-sm">
                          {children}
                        </code>
                      ),
                    }}
                  >
                    {formatMarkdownContent(agent.content)}
                  </ReactMarkdown>
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>
        ))}
      </div>
      <Toaster />
    </div>
  );
};

export default AnalysisPage;
