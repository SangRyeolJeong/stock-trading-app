from app.schemas.market import Instrument
from app.services.instruments import parse_domestic_master, parse_overseas_master


def test_parse_domestic_master_uses_fixed_width_prefix_and_security_type() -> None:
    prefix = f"{'005930':<9}{'KR7005930003':<12}삼성전자"
    suffix = "ST" + (" " * 225)

    result = parse_domestic_master((prefix + suffix).encode("cp949"), "KOSPI", 228)

    assert result == [
        Instrument(
            symbol="005930",
            name="삼성전자",
            market="KOSPI",
            exchange_code="KRX",
            currency="KRW",
            asset_type="stock",
            country="KR",
        )
    ]


def test_parse_domestic_master_recognizes_etf_group_code() -> None:
    prefix = f"{'360750':<9}{'KR7360750004':<12}TIGER 미국S&P500"
    suffix = "EF" + (" " * 225)

    result = parse_domestic_master((prefix + suffix).encode("cp949"), "KOSPI", 228)

    assert result[0].symbol == "360750"
    assert result[0].asset_type == "etf"


def test_parse_overseas_master_maps_etf_and_exchange() -> None:
    header = "\t".join(["header"] * 10)
    row = "\t".join(
        ["US", "NASD", "NAS", "NASDAQ", "QQQM", "QQQM", "인베스코 나스닥100 ETF", "Invesco NASDAQ 100 ETF", "3", "USD"]
    )

    result = parse_overseas_master(f"{header}\n{row}".encode("cp949"), "NASDAQ", "NAS")

    assert len(result) == 1
    assert result[0].symbol == "QQQM"
    assert result[0].asset_type == "etf"
    assert result[0].exchange_code == "NAS"
