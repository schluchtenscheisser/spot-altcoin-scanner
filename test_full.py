from scanner.clients.mexc_client import MEXCClient

client = MEXCClient()

# Test 1: Universe
symbols = client.get_spot_usdt_symbols()
print(f'✅ Universe: {len(symbols)} USDT pairs')

# Test 2: 24h Tickers
tickers = client.get_24h_tickers()
print(f'✅ Tickers: {len(tickers)} entries')

# Test 3: Klines (BTC)
klines = client.get_klines('BTCUSDT', '1d', limit=5)
print(f'✅ Klines: {len(klines)} candles for BTCUSDT')
print(f'   Latest close: {klines[-1][4]}')

# Test 4: Multiple klines
multi = client.get_multiple_klines(['BTCUSDT', 'ETHUSDT'], '1d', limit=3)
print(f'✅ Multi-klines: {len(multi)} symbols fetched')

print()
print('🎉 MEXC Client vollständig funktional!')
