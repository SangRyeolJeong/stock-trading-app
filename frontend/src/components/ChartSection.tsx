import { useEffect, useRef } from 'react';
import { CandlestickData, ColorType, createChart, IChartApi, ISeriesApi, Time } from 'lightweight-charts';

interface ChartSectionProps {
  symbol: string;
}

function buildData(): CandlestickData<Time>[] {
  const values = [
    [226.3, 227.8, 225.7, 227.1], [227.1, 228.4, 226.6, 227.8], [227.8, 228.1, 226.2, 226.9],
    [226.9, 227.5, 225.8, 226.2], [226.2, 227.7, 225.9, 227.3], [227.3, 228.8, 226.9, 228.4],
    [228.4, 229.1, 227.6, 228.0], [228.0, 229.7, 227.8, 229.4], [229.4, 230.2, 228.9, 229.2],
    [229.2, 230.6, 228.7, 230.1], [230.1, 231.0, 229.6, 230.7], [230.7, 231.5, 230.0, 230.4],
    [230.4, 230.9, 229.2, 229.7], [229.7, 230.3, 228.8, 229.1], [229.1, 230.1, 228.5, 229.8],
    [229.8, 230.7, 229.4, 230.5], [230.5, 231.4, 230.1, 231.0], [231.0, 231.6, 230.4, 230.8],
    [230.8, 232.0, 230.5, 231.7], [231.7, 232.4, 231.2, 232.1], [232.1, 232.5, 231.0, 231.3],
    [231.3, 232.1, 230.7, 231.9], [231.9, 232.7, 231.4, 232.4], [232.4, 233.1, 231.8, 232.0],
    [232.0, 232.4, 231.1, 231.5], [231.5, 232.0, 230.9, 231.2], [231.2, 232.1, 230.8, 231.8],
    [231.8, 232.6, 231.4, 232.2], [232.2, 232.8, 231.6, 232.5], [232.5, 233.08, 231.2, 231.72],
  ];
  const start = Math.floor(Date.now() / 1000) - values.length * 3600;
  return values.map(([open, high, low, close], index) => ({
    time: (start + index * 3600) as Time,
    open, high, low, close,
  }));
}

export default function ChartSection({ symbol }: ChartSectionProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: '#151922' }, textColor: '#6f7888', fontFamily: 'Pretendard, Inter, sans-serif', fontSize: 11 },
      grid: { vertLines: { color: '#202631' }, horzLines: { color: '#202631' } },
      rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.12, bottom: 0.12 } },
      timeScale: { borderVisible: false, timeVisible: true, secondsVisible: false, rightOffset: 3, barSpacing: 13 },
      crosshair: { vertLine: { color: '#596477', labelBackgroundColor: '#394355' }, horzLine: { color: '#596477', labelBackgroundColor: '#394355' } },
      localization: { priceFormatter: (price: number) => `$${price.toFixed(2)}` },
    });
    const series = chart.addCandlestickSeries({
      upColor: '#ee5d75', downColor: '#4c82ff', borderUpColor: '#ee5d75', borderDownColor: '#4c82ff', wickUpColor: '#ee5d75', wickDownColor: '#4c82ff',
    });
    series.setData(buildData());
    chart.timeScale().fitContent();
    chartRef.current = chart;
    seriesRef.current = series;
    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [symbol]);

  return <div ref={containerRef} className="chart-canvas" aria-label={`${symbol} 가격 차트`} />;
}
