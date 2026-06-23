select ticker,
       date,
       open,
       high,
       low,
       close,
       volume
  from {{ source('financial', 'raw_prices') }}
 where date is not null
   and open is not null
   and close is not null