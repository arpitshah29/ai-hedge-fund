import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';

interface TradeRecord {
  date: string;
  action: string;
  price: number;
  amount: number;
  value: number;
}

const BacktestPage = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<TradeRecord[]>([]);
  const [stats, setStats] = useState({
    totalTrades: 0,
    profitableTrades: 0,
    totalReturn: 0,
  });

  const runBacktest = async () => {
    setLoading(true);
    try {
      // TODO: Implement API call for backtest
      await new Promise(resolve => setTimeout(resolve, 2000));
      // Simulated backtest results
      const sampleResults: TradeRecord[] = [
        { date: '2024-01-01', action: 'Buy', price: 42150.23, amount: 0.5, value: 21075.115 },
        { date: '2024-01-15', action: 'Sell', price: 43500.00, amount: 0.5, value: 21750.00 },
        { date: '2024-02-01', action: 'Buy', price: 41800.00, amount: 0.6, value: 25080.00 },
        { date: '2024-02-15', action: 'Sell', price: 44200.00, amount: 0.6, value: 26520.00 },
      ];

      setResults(sampleResults);
      setStats({
        totalTrades: 4,
        profitableTrades: 2,
        totalReturn: 8.5,
      });
    } catch (error) {
      console.error('Backtest failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">BTC Backtest</h1>

      <Card>
        <CardHeader>
          <CardTitle>Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">End Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          <Button onClick={runBacktest} disabled={loading || !startDate || !endDate}>
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Run Backtest
          </Button>
        </CardContent>
      </Card>

      {results.length > 0 && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Backtest Statistics</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Trades</p>
                <p className="text-2xl font-bold">{stats.totalTrades}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Profitable Trades</p>
                <p className="text-2xl font-bold">{stats.profitableTrades}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Return</p>
                <p className="text-2xl font-bold text-green-500">+{stats.totalReturn}%</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Trade History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b">
                      <th className="pb-2">Date</th>
                      <th className="pb-2">Action</th>
                      <th className="pb-2">Price</th>
                      <th className="pb-2">Amount</th>
                      <th className="pb-2">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((record, index) => (
                      <tr key={index} className="border-b">
                        <td className="py-2">{record.date}</td>
                        <td className="py-2">{record.action}</td>
                        <td className="py-2">${record.price.toLocaleString()}</td>
                        <td className="py-2">{record.amount} BTC</td>
                        <td className="py-2">${record.value.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default BacktestPage;
