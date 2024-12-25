import { useState, useMemo, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useDebounce } from 'use-debounce';

interface Cryptocurrency {
  id: string;
  symbol: string;
  name: string;
  rank: number;
  platform?: string;
}

interface CryptoSelectProps {
  cryptocurrencies: Cryptocurrency[];
  value?: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export const CryptoSelect = ({ 
  cryptocurrencies, 
  value = "BTC",
  onChange, 
  disabled 
}: CryptoSelectProps) => {
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebounce(search, 300);

  useEffect(() => {
    if (value && cryptocurrencies.length > 0) {
      const selectedCrypto = cryptocurrencies.find(crypto => crypto.symbol === value);
      if (!selectedCrypto) {
        onChange(cryptocurrencies[0].symbol);
      }
    }
  }, [cryptocurrencies]);

  const filteredCryptos = useMemo(() => {
    if (!debouncedSearch) return cryptocurrencies;
    
    const searchTerm = debouncedSearch.toLowerCase();
    return cryptocurrencies
      .map(crypto => {
        const nameMatch = crypto.name.toLowerCase().includes(searchTerm);
        const symbolMatch = crypto.symbol.toLowerCase().includes(searchTerm);
        const exactMatch = crypto.symbol.toLowerCase() === searchTerm || 
                          crypto.name.toLowerCase() === searchTerm;
        const score = exactMatch ? 3 : (nameMatch ? 2 : (symbolMatch ? 1 : 0));
        
        return { ...crypto, score };
      })
      .filter(crypto => crypto.score > 0)
      .sort((a, b) => b.score - a.score);
  }, [cryptocurrencies, debouncedSearch]);

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger className="w-[280px]">
        <SelectValue>
          {value && cryptocurrencies.find(c => c.symbol === value)?.name || 'Select Cryptocurrency'}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        <div className="p-2">
          <Input
            placeholder="Search cryptocurrencies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="mb-2"
          />
        </div>
        <ScrollArea className="h-[300px]">
          {filteredCryptos.length > 0 ? (
            filteredCryptos.map((crypto) => (
              <SelectItem key={crypto.symbol} value={crypto.symbol}>
                {`${crypto.name} (${crypto.symbol})`}
              </SelectItem>
            ))
          ) : (
            <div className="p-2 text-center text-sm text-muted-foreground">
              No cryptocurrencies found
            </div>
          )}
        </ScrollArea>
      </SelectContent>
    </Select>
  );
}; 