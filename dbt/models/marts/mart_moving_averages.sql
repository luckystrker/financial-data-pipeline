with prices as (
    select ticker,
           date,
           close
      from {{ ref('stg_prices') }}
)
select ticker,
       date,
       close,
       round(avg(close) over (partition by ticker order by date rows between 6 preceding and current row),
             4) as ma_7d,
       round(avg(close) over (partition by ticker order by date rows between 29 preceding and current row),
             4) as ma_30d
  from prices