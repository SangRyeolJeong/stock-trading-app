import React from 'react';
import useStockStore from '../store/useStockStore';

interface OrderBookProps {
  onOrderClick: (price: string, type: 'buy' | 'sell') => void;
}

const OrderBook: React.FC<OrderBookProps> = ({ onOrderClick }) => {
  const { orderBook } = useStockStore();

  if (!orderBook) {
    return <div className="text-toss_text_secondary">호가 정보를 불러오는 중...</div>;
  }

  const renderOrderBookEntries = (entries: { price: string; quantity: string }[], type: 'buy' | 'sell') => {
    return entries.map((entry, index) => (
      <div
        key={index}
        className={`flex justify-between items-center py-1 px-2 rounded-md cursor-pointer
          ${type === 'sell' ? 'hover:bg-red-700' : 'hover:bg-blue-700'}`}
        onClick={() => onOrderClick(entry.price, type)}
      >
        <span className={`${type === 'sell' ? 'text-toss_red' : 'text-toss_blue'} font-semibold`}>{entry.price}</span>
        <span className="text-toss_text_primary">{entry.quantity}</span>
      </div>
    ));
  };

  return (
    <div className="bg-toss_navy p-4 rounded-lg shadow-lg h-full flex flex-col">
      <h2 className="text-xl font-bold text-toss_text_primary mb-4">호가창</h2>
      <div className="flex flex-col flex-grow">
        <div className="flex-grow bg-[#2A1A2E] rounded-md p-2 mb-2">
          <h3 className="text-toss_red text-lg font-bold mb-2">매도 호가</h3>
          {renderOrderBookEntries(orderBook.sell, 'sell')}
        </div>
        <div className="flex-grow bg-[#1A2A3E] rounded-md p-2 mt-2">
          <h3 className="text-toss_blue text-lg font-bold mb-2">매수 호가</h3>
          {renderOrderBookEntries(orderBook.buy, 'buy')}
        </div>
      </div>
    </div>
  );
};

export default OrderBook;
