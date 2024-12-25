import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

// Define the structure for API keys
interface ApiKeys {
  openai: string;
  anthropic: string;
  coinmarketcap: string;
}

const ConfigPage = () => {
  const { toast } = useToast();
  
  // Initialize API keys from environment variables
  const [apiKeys, setApiKeys] = useState<ApiKeys>({
    openai: import.meta.env.VITE_OPENAI_API_KEY || '',
    anthropic: import.meta.env.VITE_ANTHROPIC_API_KEY || '',
    coinmarketcap: import.meta.env.VITE_COINMARKETCAP_API_KEY || '',
  });
  
  // Loading state for form submission
  const [isLoading, setIsLoading] = useState(false);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // TODO: Implement API call to save keys
      // For now, just show success toast
      toast({
        title: "Configuration Saved",
        description: "Your API keys have been successfully updated.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save configuration. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>API Configuration</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* OpenAI API Key Input */}
          <div className="space-y-2">
            <label htmlFor="openai">OpenAI API Key</label>
            <Input
              id="openai"
              type="password"
              value={apiKeys.openai}
              onChange={(e) => setApiKeys(prev => ({...prev, openai: e.target.value}))}
              placeholder="Enter your OpenAI API key"
            />
          </div>

          {/* Anthropic API Key Input */}
          <div className="space-y-2">
            <label htmlFor="anthropic">Anthropic API Key</label>
            <Input
              id="anthropic"
              type="password"
              value={apiKeys.anthropic}
              onChange={(e) => setApiKeys(prev => ({...prev, anthropic: e.target.value}))}
              placeholder="Enter your Anthropic API key"
            />
          </div>

          {/* CoinMarketCap API Key Input */}
          <div className="space-y-2">
            <label htmlFor="coinmarketcap">CoinMarketCap API Key</label>
            <Input
              id="coinmarketcap"
              type="password"
              value={apiKeys.coinmarketcap}
              onChange={(e) => setApiKeys(prev => ({...prev, coinmarketcap: e.target.value}))}
              placeholder="Enter your CoinMarketCap API key"
            />
          </div>

          {/* Submit Button */}
          <Button type="submit" disabled={isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Configuration
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default ConfigPage;
