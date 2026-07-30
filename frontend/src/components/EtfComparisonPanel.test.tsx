import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import type { EtfComparison, EtfProfile } from '../types/api';
import { EtfComparisonPanel } from './EtfComparisonPanel';

const getEtfsMock = vi.hoisted(() => vi.fn());
const compareEtfsMock = vi.hoisted(() => vi.fn());

vi.mock('../services/marketApi', () => ({
  marketApi: {
    getEtfs: getEtfsMock,
    compareEtfs: compareEtfsMock,
  },
}));

function profile(symbol: string, expenseRatio: string): EtfProfile {
  return {
    symbol,
    name: symbol === 'QQQM' ? 'Invesco NASDAQ 100 ETF' : 'Invesco QQQ',
    issuer: 'Invesco',
    listing_country: 'US',
    trading_currency: 'USD',
    underlying_index: 'Nasdaq-100 Index',
    expense_ratio_pct: expenseRatio,
    holdings_count: 102,
    inception_date: symbol === 'QQQM' ? '2020-10-13' : '1999-03-10',
    facts_as_of: '2026-06-30',
    holdings_as_of: '2026-03-31',
    top_holdings_coverage_pct: '46.50',
    top_holdings: [
      { symbol: 'NVDA', name: 'NVIDIA', weight_pct: '8.50' },
    ],
    source_url: `https://example.com/${symbol}`,
    holdings_source_url: `https://example.com/${symbol}/holdings`,
  };
}

describe('EtfComparisonPanel', () => {
  it('prioritizes a same-index alternative and renders the server calculation', async () => {
    const qqqm = profile('QQQM', '0.15');
    const qqq = profile('QQQ', '0.18');
    const comparison: EtfComparison = {
      left: qqqm,
      right: qqq,
      same_underlying_index: true,
      top_holdings_overlap_pct: '98.50',
      common_top_holdings_count: 1,
      common_top_holdings: [{
        symbol: 'NVDA',
        name: 'NVIDIA',
        left_weight_pct: '8.40',
        right_weight_pct: '8.67',
        shared_weight_pct: '8.40',
      }],
      lower_expense_symbol: 'QQQM',
      comparison_principal_krw: '10000000',
      annual_fee_difference_krw: '3000',
      interpretation: '같은 지수 비교 설명',
      formula: '중복도 계산식',
      data_version: 'ETF-COMPARE-2026.07',
      disclaimer: '교육용 비교',
    };
    getEtfsMock.mockResolvedValue({
      items: [qqqm, qqq],
      data_version: comparison.data_version,
      disclaimer: comparison.disclaimer,
    });
    compareEtfsMock.mockResolvedValue(comparison);
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <EtfComparisonPanel symbol="QQQM" />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText('98.5%')).toBeInTheDocument();
    expect(screen.getByText('연 3,000원')).toBeInTheDocument();
    expect(screen.getByText('같은 기초지수')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'QQQ · Nasdaq-100 Index' })).toBeInTheDocument();
    expect(compareEtfsMock).toHaveBeenCalledWith('QQQM', 'QQQ');
  });

  it('labels cross-listed comparisons and shows the tax and currency caution', async () => {
    const kodex = {
      ...profile('379810', '0.0062'),
      name: 'KODEX 미국나스닥100',
      issuer: '삼성자산운용',
      listing_country: 'KR' as const,
      trading_currency: 'KRW' as const,
    };
    const qqqm = profile('QQQM', '0.15');
    const comparison: EtfComparison = {
      left: kodex,
      right: qqqm,
      same_underlying_index: true,
      top_holdings_overlap_pct: '92.00',
      common_top_holdings_count: 1,
      common_top_holdings: [{
        symbol: 'NVDA',
        name: 'NVIDIA',
        left_weight_pct: '7.66',
        right_weight_pct: '8.40',
        shared_weight_pct: '7.66',
      }],
      lower_expense_symbol: '379810',
      comparison_principal_krw: '10000000',
      annual_fee_difference_krw: '14380',
      interpretation: '상장국이 다른 같은 지수 비교',
      formula: '중복도 계산식',
      data_version: 'ETF-COMPARE-2026.07',
      disclaimer: '한국·미국 상장 ETF는 세금·환전·거래시간이 다릅니다.',
    };
    getEtfsMock.mockResolvedValue({
      items: [kodex, qqqm],
      data_version: comparison.data_version,
      disclaimer: comparison.disclaimer,
    });
    compareEtfsMock.mockResolvedValue(comparison);
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <EtfComparisonPanel symbol="379810" />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText('92%')).toBeInTheDocument();
    expect(screen.getByText('한국 상장')).toBeInTheDocument();
    expect(screen.getByText('KRW 거래')).toBeInTheDocument();
    expect(screen.getByText(/과세·환전·/)).toBeInTheDocument();
    expect(compareEtfsMock).toHaveBeenCalledWith('379810', 'QQQM');
  });
});
