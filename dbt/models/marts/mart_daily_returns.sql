-- mart_daily_returns: daily percentage return per ticker
with prices as (
    select ticker,
           date,
           close
      from {{ ref('stg_prices') }}
)

select ticker,
       date,
       close,
       round((close - lagInFrame(close) over (partition by ticker order by date))
             / lagInFrame(close) over (partition by ticker order by date)
             * 100,
             4) as daily_return_pct
  from prices