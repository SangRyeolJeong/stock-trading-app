from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

from app.schemas.market import (
    EtfCatalogResponse,
    EtfCommonHolding,
    EtfComparison,
    EtfHolding,
    EtfProfile,
)

DATA_VERSION = "ETF-COMPARE-2026.08"
COMPARISON_PRINCIPAL_KRW = Decimal("10000000")
SNAPSHOT_MAX_AGE_DAYS = {
    "QQQM": 190,
    "QQQ": 190,
    "SPY": 14,
    "VOO": 95,
    "379800": 45,
    "379810": 45,
    "360750": 45,
    "133690": 45,
}
DISCLAIMER = (
    "운용사 공식 자료의 기준일 스냅샷을 사용한 교육용 비교입니다. "
    "표시 총보수는 기타비용·매매비용을 포함한 실제 부담비용과 다를 수 있고, "
    "한국·미국 상장 ETF는 세금·환전·거래시간이 다릅니다. "
    "구성종목과 보수는 변경될 수 있으므로 주문 전 최신 운용사 자료를 확인하세요."
)
FORMULA = (
    "상위 구성종목 중복도 = 공통 종목별 두 ETF 비중의 최솟값 합계 ÷ "
    "두 ETF 중 더 작은 상위 종목 표시 비중 합계 × 100"
)

INVESCO_SUITE_URL = "https://www.invesco.com/us/en/solutions/innovation-suite.html"
QQQ_HOLDINGS_URL = (
    "https://www.invesco.com/us-rest/contentdetail"
    "?contentId=841e411c-a1eb-4541-8cb8-0fa603abea81&dnsName=us"
)
QQQM_HOLDINGS_URL = (
    "https://www.invesco.com/content/dam/invesco/us/en/product-documents/etf/commentary/"
    "monthly-qqqm-commentary-retail-use-.pdf"
)
SPY_URL = (
    "https://www.ssga.com/us/en/intermediary/etfs/"
    "state-street-spdr-sp-500-etf-trust-spy"
)
VOO_URL = "https://investor.vanguard.com/investment-products/etfs/profile/voo"
KODEX_SP500_URL = "https://www.samsungfund.com/etf/product/view.do?id=2ETFE4"
KODEX_NASDAQ100_URL = "https://www.samsungfund.com/etf/product/view.do?id=2ETFE3"
TIGER_SP500_URL = (
    "https://www.tigeretf.com/ko/product/search/detail/index.do"
    "?ksdFund=KR7360750004&otherPage=asset"
)
TIGER_NASDAQ100_URL = (
    "https://www.tigeretf.com/ko/product/search/detail/index.do"
    "?ksdFund=KR7133690008&otherPage=asset"
)


def _holding(symbol: str, name: str, weight_pct: str) -> EtfHolding:
    return EtfHolding(symbol=symbol, name=name, weight_pct=Decimal(weight_pct))


def _profile(
    *,
    symbol: str,
    name: str,
    issuer: str,
    listing_country: Literal["US", "KR"],
    trading_currency: Literal["USD", "KRW"],
    underlying_index: str,
    expense_ratio_pct: str,
    holdings_count: int,
    inception_date: date,
    facts_as_of: date,
    holdings_as_of: date,
    top_holdings: list[EtfHolding],
    source_url: str,
    holdings_source_url: str,
) -> EtfProfile:
    coverage = sum((holding.weight_pct for holding in top_holdings), Decimal("0"))
    return EtfProfile(
        symbol=symbol,
        name=name,
        issuer=issuer,
        listing_country=listing_country,
        trading_currency=trading_currency,
        underlying_index=underlying_index,
        expense_ratio_pct=Decimal(expense_ratio_pct),
        holdings_count=holdings_count,
        inception_date=inception_date,
        facts_as_of=facts_as_of,
        holdings_as_of=holdings_as_of,
        top_holdings_coverage_pct=coverage,
        top_holdings=top_holdings,
        source_url=source_url,
        holdings_source_url=holdings_source_url,
    )


ETF_PROFILES = {
    "QQQM": _profile(
        symbol="QQQM",
        name="Invesco NASDAQ 100 ETF",
        issuer="Invesco",
        listing_country="US",
        trading_currency="USD",
        underlying_index="Nasdaq-100 Index",
        expense_ratio_pct="0.15",
        holdings_count=102,
        inception_date=date(2020, 10, 13),
        facts_as_of=date(2026, 6, 30),
        holdings_as_of=date(2026, 2, 28),
        top_holdings=[
            _holding("NVDA", "NVIDIA", "8.40"),
            _holding("AAPL", "Apple", "7.61"),
            _holding("MSFT", "Microsoft", "5.69"),
            _holding("AMZN", "Amazon", "4.38"),
            _holding("TSLA", "Tesla", "3.92"),
            _holding("META", "Meta Platforms A", "3.71"),
            _holding("GOOGL", "Alphabet A", "3.54"),
            _holding("WMT", "Walmart", "3.37"),
            _holding("GOOG", "Alphabet C", "3.28"),
            _holding("AVGO", "Broadcom", "2.94"),
        ],
        source_url=INVESCO_SUITE_URL,
        holdings_source_url=QQQM_HOLDINGS_URL,
    ),
    "QQQ": _profile(
        symbol="QQQ",
        name="Invesco QQQ",
        issuer="Invesco",
        listing_country="US",
        trading_currency="USD",
        underlying_index="Nasdaq-100 Index",
        expense_ratio_pct="0.18",
        holdings_count=102,
        inception_date=date(1999, 3, 10),
        facts_as_of=date(2026, 3, 31),
        holdings_as_of=date(2026, 3, 31),
        top_holdings=[
            _holding("NVDA", "NVIDIA", "8.67"),
            _holding("AAPL", "Apple", "7.62"),
            _holding("MSFT", "Microsoft", "5.62"),
            _holding("AMZN", "Amazon", "4.58"),
            _holding("TSLA", "Tesla", "3.80"),
            _holding("META", "Meta Platforms A", "3.45"),
            _holding("WMT", "Walmart", "3.43"),
            _holding("GOOGL", "Alphabet A", "3.43"),
            _holding("GOOG", "Alphabet C", "3.19"),
            _holding("AVGO", "Broadcom", "3.00"),
        ],
        source_url=INVESCO_SUITE_URL,
        holdings_source_url=QQQ_HOLDINGS_URL,
    ),
    "SPY": _profile(
        symbol="SPY",
        name="State Street SPDR S&P 500 ETF Trust",
        issuer="State Street",
        listing_country="US",
        trading_currency="USD",
        underlying_index="S&P 500 Index",
        expense_ratio_pct="0.0945",
        holdings_count=504,
        inception_date=date(1993, 1, 22),
        facts_as_of=date(2026, 7, 31),
        holdings_as_of=date(2026, 7, 30),
        top_holdings=[
            _holding("AAPL", "Apple", "7.65"),
            _holding("NVDA", "NVIDIA", "7.38"),
            _holding("MSFT", "Microsoft", "5.24"),
            _holding("AMZN", "Amazon", "3.60"),
            _holding("GOOGL", "Alphabet A", "3.06"),
            _holding("AVGO", "Broadcom", "2.87"),
            _holding("GOOG", "Alphabet C", "2.46"),
            _holding("META", "Meta Platforms A", "1.85"),
            _holding("MU", "Micron Technology", "1.54"),
            _holding("JPM", "JPMorgan Chase", "1.47"),
        ],
        source_url=SPY_URL,
        holdings_source_url=SPY_URL,
    ),
    "VOO": _profile(
        symbol="VOO",
        name="Vanguard S&P 500 ETF",
        issuer="Vanguard",
        listing_country="US",
        trading_currency="USD",
        underlying_index="S&P 500 Index",
        expense_ratio_pct="0.03",
        holdings_count=505,
        inception_date=date(2010, 9, 7),
        facts_as_of=date(2026, 6, 30),
        holdings_as_of=date(2026, 5, 31),
        top_holdings=[
            _holding("NVDA", "NVIDIA", "7.89"),
            _holding("AAPL", "Apple", "7.05"),
            _holding("MSFT", "Microsoft", "5.14"),
            _holding("AMZN", "Amazon", "4.07"),
            _holding("GOOGL", "Alphabet A", "3.41"),
            _holding("AVGO", "Broadcom", "3.26"),
            _holding("GOOG", "Alphabet C", "2.71"),
            _holding("META", "Meta Platforms A", "2.13"),
            _holding("TSLA", "Tesla", "1.89"),
            _holding("MU", "Micron Technology", "1.68"),
        ],
        source_url=VOO_URL,
        holdings_source_url=VOO_URL,
    ),
    "379800": _profile(
        symbol="379800",
        name="KODEX 미국S&P500",
        issuer="삼성자산운용",
        listing_country="KR",
        trading_currency="KRW",
        underlying_index="S&P 500 Index",
        expense_ratio_pct="0.0062",
        holdings_count=506,
        inception_date=date(2021, 4, 9),
        facts_as_of=date(2026, 7, 31),
        holdings_as_of=date(2026, 7, 3),
        top_holdings=[
            _holding("NVDA", "NVIDIA", "7.34"),
            _holding("AAPL", "Apple", "7.05"),
            _holding("MSFT", "Microsoft", "4.51"),
            _holding("AMZN", "Amazon", "3.69"),
            _holding("GOOGL", "Alphabet A", "3.28"),
            _holding("AVGO", "Broadcom", "2.65"),
            _holding("GOOG", "Alphabet C", "2.62"),
            _holding("META", "Meta Platforms A", "2.10"),
            _holding("TSLA", "Tesla", "1.76"),
        ],
        source_url=KODEX_SP500_URL,
        holdings_source_url=KODEX_SP500_URL,
    ),
    "379810": _profile(
        symbol="379810",
        name="KODEX 미국나스닥100",
        issuer="삼성자산운용",
        listing_country="KR",
        trading_currency="KRW",
        underlying_index="Nasdaq-100 Index",
        expense_ratio_pct="0.0062",
        holdings_count=105,
        inception_date=date(2021, 4, 9),
        facts_as_of=date(2026, 7, 31),
        holdings_as_of=date(2026, 7, 8),
        top_holdings=[
            _holding("NVDA", "NVIDIA", "7.66"),
            _holding("AAPL", "Apple", "7.33"),
            _holding("MU", "Micron Technology", "4.70"),
            _holding("MSFT", "Microsoft", "4.64"),
            _holding("AMZN", "Amazon", "4.25"),
            _holding("AMD", "Advanced Micro Devices", "3.73"),
            _holding("GOOGL", "Alphabet A", "3.44"),
            _holding("TSLA", "Tesla", "3.24"),
            _holding("GOOG", "Alphabet C", "3.19"),
            _holding("META", "Meta Platforms A", "2.93"),
        ],
        source_url=KODEX_NASDAQ100_URL,
        holdings_source_url=KODEX_NASDAQ100_URL,
    ),
    "360750": _profile(
        symbol="360750",
        name="TIGER 미국S&P500",
        issuer="미래에셋자산운용",
        listing_country="KR",
        trading_currency="KRW",
        underlying_index="S&P 500 Index",
        expense_ratio_pct="0.0068",
        holdings_count=504,
        inception_date=date(2020, 8, 6),
        facts_as_of=date(2026, 7, 31),
        holdings_as_of=date(2026, 7, 31),
        top_holdings=[
            _holding("AAPL", "Apple", "7.65"),
            _holding("NVDA", "NVIDIA", "7.38"),
            _holding("MSFT", "Microsoft", "5.24"),
            _holding("AMZN", "Amazon", "3.60"),
            _holding("GOOGL", "Alphabet A", "3.06"),
            _holding("AVGO", "Broadcom", "2.87"),
            _holding("GOOG", "Alphabet C", "2.46"),
            _holding("META", "Meta Platforms A", "1.85"),
            _holding("MU", "Micron Technology", "1.54"),
            _holding("JPM", "JPMorgan Chase", "1.47"),
        ],
        source_url=TIGER_SP500_URL,
        holdings_source_url=TIGER_SP500_URL,
    ),
    "133690": _profile(
        symbol="133690",
        name="TIGER 미국나스닥100",
        issuer="미래에셋자산운용",
        listing_country="KR",
        trading_currency="KRW",
        underlying_index="Nasdaq-100 Index",
        expense_ratio_pct="0.0068",
        holdings_count=104,
        inception_date=date(2010, 10, 15),
        facts_as_of=date(2026, 7, 31),
        holdings_as_of=date(2026, 7, 31),
        top_holdings=[
            _holding("AAPL", "Apple", "8.16"),
            _holding("NVDA", "NVIDIA", "7.86"),
            _holding("MSFT", "Microsoft", "5.58"),
            _holding("MU", "Micron Technology", "4.53"),
            _holding("AMZN", "Amazon", "4.22"),
            _holding("AMD", "Advanced Micro Devices", "3.64"),
            _holding("GOOGL", "Alphabet A", "3.24"),
            _holding("AVGO", "Broadcom", "3.06"),
            _holding("GOOG", "Alphabet C", "3.03"),
            _holding("META", "Meta Platforms A", "2.66"),
        ],
        source_url=TIGER_NASDAQ100_URL,
        holdings_source_url=TIGER_NASDAQ100_URL,
    ),
}


def stale_etf_symbols(as_of: date | None = None) -> list[str]:
    reference_date = as_of or date.today()
    return sorted(
        profile.symbol
        for profile in ETF_PROFILES.values()
        if min(profile.facts_as_of, profile.holdings_as_of)
        < reference_date - timedelta(days=SNAPSHOT_MAX_AGE_DAYS[profile.symbol])
        or max(profile.facts_as_of, profile.holdings_as_of) > reference_date
    )


def list_etfs() -> EtfCatalogResponse:
    return EtfCatalogResponse(
        items=list(ETF_PROFILES.values()),
        data_version=DATA_VERSION,
        disclaimer=DISCLAIMER,
    )


def compare_etfs(left_symbol: str, right_symbol: str) -> EtfComparison:
    left_key = left_symbol.strip().upper()
    right_key = right_symbol.strip().upper()
    if left_key == right_key:
        raise ValueError("서로 다른 ETF 두 개를 선택해야 합니다.")

    try:
        left = ETF_PROFILES[left_key]
        right = ETF_PROFILES[right_key]
    except KeyError as exc:
        raise KeyError("비교 데이터가 없는 ETF입니다.") from exc

    right_holdings = {holding.symbol: holding for holding in right.top_holdings}
    common = [
        EtfCommonHolding(
            symbol=holding.symbol,
            name=holding.name,
            left_weight_pct=holding.weight_pct,
            right_weight_pct=right_holdings[holding.symbol].weight_pct,
            shared_weight_pct=min(holding.weight_pct, right_holdings[holding.symbol].weight_pct),
        )
        for holding in left.top_holdings
        if holding.symbol in right_holdings
    ]
    common.sort(key=lambda holding: holding.shared_weight_pct, reverse=True)
    shared_weight = sum((holding.shared_weight_pct for holding in common), Decimal("0"))
    coverage_base = min(left.top_holdings_coverage_pct, right.top_holdings_coverage_pct)
    overlap = (
        (shared_weight / coverage_base * Decimal("100")).quantize(Decimal("0.01"))
        if coverage_base > 0
        else Decimal("0")
    )

    fee_gap_pct = abs(left.expense_ratio_pct - right.expense_ratio_pct)
    annual_fee_difference = (
        COMPARISON_PRINCIPAL_KRW * fee_gap_pct / Decimal("100")
    ).quantize(Decimal("1"))
    if left.expense_ratio_pct == right.expense_ratio_pct:
        lower_expense_symbol = None
    elif left.expense_ratio_pct < right.expense_ratio_pct:
        lower_expense_symbol = left.symbol
    else:
        lower_expense_symbol = right.symbol

    same_index = left.underlying_index == right.underlying_index
    cross_listing = left.listing_country != right.listing_country
    if same_index and overlap >= Decimal("90"):
        interpretation = (
            "같은 지수를 추종하고 상위 구성종목도 매우 유사합니다. "
            "장기 보유 비용과 거래량·호가를 함께 비교하세요."
        )
    elif overlap >= Decimal("60"):
        interpretation = (
            "주요 대형주 노출이 상당 부분 겹칩니다. 두 ETF를 함께 보유해도 "
            "생각보다 분산 효과가 작을 수 있습니다."
        )
    else:
        interpretation = (
            "상위 구성종목의 겹침이 상대적으로 낮습니다. 지수 성격과 섹터 비중을 "
            "추가로 확인하세요."
        )
    if cross_listing:
        interpretation += (
            " 상장국이 달라 명목 총보수만으로 결정하지 말고 세금·환전·거래시간과 "
            "기타비용을 함께 확인하세요."
        )

    return EtfComparison(
        left=left,
        right=right,
        same_underlying_index=same_index,
        top_holdings_overlap_pct=overlap,
        common_top_holdings_count=len(common),
        common_top_holdings=common,
        lower_expense_symbol=lower_expense_symbol,
        comparison_principal_krw=COMPARISON_PRINCIPAL_KRW,
        annual_fee_difference_krw=annual_fee_difference,
        interpretation=interpretation,
        formula=FORMULA,
        data_version=DATA_VERSION,
        disclaimer=DISCLAIMER,
    )
