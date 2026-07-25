
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    cma_balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL, -- Stock or ETF symbol
    average_buy_price DECIMAL(15, 2) NOT NULL,
    quantity INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, symbol)
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE SET NULL, -- Can be NULL if it's a new buy order
    symbol VARCHAR(10) NOT NULL,
    order_type VARCHAR(50) NOT NULL, -- e.g., 'buy', 'sell'
    price DECIMAL(15, 2) NOT NULL,
    quantity INT NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE etf_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL UNIQUE, -- ETF 종목코드
    name VARCHAR(255) NOT NULL,       -- ETF 종목명
    issuer VARCHAR(255) NOT NULL,     -- 운용사
    expense_ratio DECIMAL(5, 4) NOT NULL, -- 총보수 (e.g., 0.0050 for 0.50%)
    assets_under_management DECIMAL(18, 2), -- 자산규모
    covered_call_generation VARCHAR(50), -- 커버드콜 세대 구분 (e.g., 'Generation 1', 'Generation 2')
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
