-- mart_volatility: weekly volatility per ticker
{{ config(order_by='(ticker, week_start)') }}

select ticker,
       toStartOfWeek(date)                          as week_start,
       count(date)                                  as trading_days,
       round(avg(daily_return_pct), 4)              as avg_return_pct,
       round(stddevSamp(daily_return_pct), 4)       as volatility_pct,
       round(min(daily_return_pct), 4)              as min_return_pct,
       round(max(daily_return_pct), 4)              as max_return_pct
  from {{ ref('mart_daily_returns') }}
 group by ticker, toStartOfWeek(date)
 order by week_start desc, ticker