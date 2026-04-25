import ccxt
from config import BINANCE_API_KEY, BINANCE_SECRET, USE_TESTNET, RISK_PERCENT, MAX_LEVERAGE_CAP


def get_exchange() -> ccxt.binanceusdm:
    exchange = ccxt.binanceusdm({
        "apiKey": BINANCE_API_KEY,
        "secret": BINANCE_SECRET,
        "options": {"defaultType": "future"},
    })
    if USE_TESTNET:
        exchange.set_sandbox_mode(True)
    exchange.load_markets()
    return exchange


def _binance_symbol(coin: str) -> str:
    """Konversi coin ke format CCXT perpetual futures"""
    coin = coin.upper().replace("USDT", "").replace("/", "")
    return f"{coin}/USDT:USDT"


def get_available_balance(exchange: ccxt.binanceusdm) -> float:
    balance = exchange.fetch_balance()
    return float(balance["USDT"]["free"])


def get_max_leverage(exchange: ccxt.binanceusdm, symbol: str) -> int:
    """Ambil leverage maksimal yang tersedia untuk symbol ini"""
    try:
        tiers = exchange.fetch_leverage_tiers([symbol])
        if symbol in tiers and tiers[symbol]:
            max_lev = int(tiers[symbol][0]["maxLeverage"])
            # Apply cap jika ada
            if MAX_LEVERAGE_CAP and MAX_LEVERAGE_CAP > 0:
                max_lev = min(max_lev, MAX_LEVERAGE_CAP)
            return max_lev
    except Exception as e:
        print(f"[Binance] Gagal ambil leverage tiers: {e}")
    # Fallback
    return MAX_LEVERAGE_CAP if MAX_LEVERAGE_CAP else 20


def calculate_quantity(entry: float, sl: float, balance: float, risk_pct: float) -> float:
    """
    Hitung ukuran posisi berdasarkan risk management 1%.
    Rumus: quantity = risk_amount / |entry - sl|
    """
    risk_amount = balance * (risk_pct / 100)
    sl_distance = abs(entry - sl)
    if sl_distance == 0:
        raise ValueError("Entry dan SL tidak boleh sama persis")
    return risk_amount / sl_distance


def _split_tp_quantities(total_qty: float, tp_count: int) -> list[float]:
    """Bagi kuantitas rata ke semua TP, sisa ke TP terakhir"""
    if tp_count == 1:
        return [total_qty]
    base = round(total_qty / tp_count, 8)
    parts = [base] * (tp_count - 1)
    parts.append(round(total_qty - base * (tp_count - 1), 8))
    return parts


def open_trade(signal: dict) -> dict:
    """
    Eksekusi trade Binance Futures berdasarkan sinyal.
    Return dict berisi detail eksekusi + semua order ID.
    """
    exchange = get_exchange()

    symbol = _binance_symbol(signal["coin"])
    direction = signal["direction"].upper()
    entry    = float(signal["entry"])
    sl       = float(signal["sl"])
    tp1      = float(signal["tp1"])
    tp2      = signal.get("tp2") and float(signal["tp2"])
    tp3      = signal.get("tp3") and float(signal["tp3"])

    # Validasi arah TP/SL
    if direction == "LONG":
        if sl >= entry:
            raise ValueError(f"SL ({sl}) harus di bawah entry ({entry}) untuk LONG")
        if tp1 <= entry:
            raise ValueError(f"TP1 ({tp1}) harus di atas entry ({entry}) untuk LONG")
        side       = "buy"
        close_side = "sell"
    else:
        if sl <= entry:
            raise ValueError(f"SL ({sl}) harus di atas entry ({entry}) untuk SHORT")
        if tp1 >= entry:
            raise ValueError(f"TP1 ({tp1}) harus di bawah entry ({entry}) untuk SHORT")
        side       = "sell"
        close_side = "buy"

    balance   = get_available_balance(exchange)
    leverage  = get_max_leverage(exchange, symbol)

    # Set leverage di Binance
    exchange.set_leverage(leverage, symbol)

    # Hitung kuantitas
    raw_qty = calculate_quantity(entry, sl, balance, RISK_PERCENT)
    quantity = float(exchange.amount_to_precision(symbol, raw_qty))

    if quantity <= 0:
        raise ValueError("Kuantitas terlalu kecil, cek balance atau perbesar jarak SL")

    orders_placed = []

    # ── 1. Market entry ───────────────────────────────────────────
    entry_order = exchange.create_order(
        symbol=symbol,
        type="market",
        side=side,
        amount=quantity,
    )
    orders_placed.append({
        "type": "entry",
        "id": entry_order["id"],
        "price": entry_order.get("average") or entry,
        "qty": quantity,
    })

    # ── 2. Stop Loss ──────────────────────────────────────────────
    sl_order = exchange.create_order(
        symbol=symbol,
        type="stop_market",
        side=close_side,
        amount=quantity,
        params={"stopPrice": sl, "reduceOnly": True},
    )
    orders_placed.append({"type": "sl", "id": sl_order["id"], "price": sl})

    # ── 3. Take Profit(s) ─────────────────────────────────────────
    tp_levels = [tp for tp in [tp1, tp2, tp3] if tp]
    tp_quantities = _split_tp_quantities(quantity, len(tp_levels))

    for i, (tp_price, tp_qty) in enumerate(zip(tp_levels, tp_quantities), start=1):
        tp_qty_precise = float(exchange.amount_to_precision(symbol, tp_qty))
        tp_order = exchange.create_order(
            symbol=symbol,
            type="take_profit_market",
            side=close_side,
            amount=tp_qty_precise,
            params={"stopPrice": tp_price, "reduceOnly": True},
        )
        orders_placed.append({
            "type": f"tp{i}",
            "id": tp_order["id"],
            "price": tp_price,
            "qty": tp_qty_precise,
        })

    return {
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "quantity": quantity,
        "leverage": leverage,
        "balance_before": balance,
        "risk_usdt": round(balance * RISK_PERCENT / 100, 2),
        "orders": orders_placed,
        "testnet": USE_TESTNET,
    }
