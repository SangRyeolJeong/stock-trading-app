import { useEffect, useRef } from 'react';
import { CandlestickData, ColorType, createChart, IChartApi, ISeriesApi, Time } from 'lightweight-charts';
import type { Candle } from '../types/api';

interface ChartSectionProps {
  symbol: string;
  currency: 'KRW' | 'USD';
  candles: Candle[];
}

export default function ChartSection({ symbol, currency, candles }: ChartSectionProps) {
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
      timeScale: { borderVisible: false, timeVisible: false, rightOffset: 3, barSpacing: 8 },
      crosshair: { vertLine: { color: '#596477', labelBackgroundColor: '#394355' }, horzLine: { color: '#596477', labelBackgroundColor: '#394355' } },
      localization: {
        priceFormatter: (price: number) => new Intl.NumberFormat(
          currency === 'KRW' ? 'ko-KR' : 'en-US',
          { style: 'currency', currency, maximumFractionDigits: currency === 'KRW' ? 0 : 2 },
        ).format(price),
      },
    });
    const series = chart.addCandlestickSeries({
      upColor: '#ee5d75',
      downColor: '#4c82ff',
      borderUpColor: '#ee5d75',
      borderDownColor: '#4c82ff',
      wickUpColor: '#ee5d75',
      wickDownColor: '#4c82ff',
      priceFormat: { type: 'price', precision: currency === 'KRW' ? 0 : 2, minMove: currency === 'KRW' ? 1 : 0.01 },
    });
    chartRef.current = chart;
    seriesRef.current = series;
    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [currency, symbol]);

  useEffect(() => {
    if (!seriesRef.current || !chartRef.current) return;
    const data: CandlestickData<Time>[] = candles.map((candle) => ({
      time: candle.date as Time,
      open: Number(candle.open),
      high: Number(candle.high),
      low: Number(candle.low),
      close: Number(candle.close),
    }));
    seriesRef.current.setData(data);
    chartRef.current.timeScale().fitContent();
  }, [candles]);

  return <div ref={containerRef} className="chart-canvas" aria-label={`${symbol} 일봉 가격 차트`} />;
}
