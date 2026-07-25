import { create } from 'zustand';

interface StockPrice {
  currentPrice: string;
  changeRate: string;
  tradeVolume: string;
}

interface OrderBookEntry {
  price: string;
  quantity: string;
}

interface OrderBook {
  sell: OrderBookEntry[];
  buy: OrderBookEntry[];
}

interface StockState {
  selectedSymbol: string | null;
  currentPrice: StockPrice | null;
  orderBook: OrderBook | null;
  setSelectedSymbol: (symbol: string) => void;
  fetchStockData: (symbol: string) => Promise<void>;
  // For real-time updates, consider a WebSocket connection or polling here
}

const useStockStore = create<StockState>((set) => ({
  selectedSymbol: null,
  currentPrice: null,
  orderBook: null,
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
  fetchStockData: async (symbol: string) => {
    // Simulate API call for current price
    const priceResponse = await fetch(`http://localhost:8000/stock/${symbol}/price`);
    const priceData = await priceResponse.json();

    // Simulate API call for order book
    const orderBookResponse = await fetch(`http://localhost:8000/stock/${symbol}/orderbook`);
    const orderBookData = await orderBookResponse.json();

    set({
      currentPrice: priceData.price.output, // Assuming API returns data in output field
      orderBook: {
        sell: orderBookData.orderbook.aspr_datas.map((data: any) => ({price: data.aspr, quantity: data.acpt_vol})),
        buy: orderBookData.orderbook.bidh_datas.map((data: any) => ({price: data.bidp, quantity: data.bidh_vol})),
      },
    });
  },
}));

export default useStockStore;
