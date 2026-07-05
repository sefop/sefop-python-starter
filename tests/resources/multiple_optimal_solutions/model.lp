\ File written by HiGHS .lp file handler
max
 obj: +100 quantity_cookie_a +100 quantity_cookie_b 
st
 weight_limit: +1 quantity_cookie_a +1 quantity_cookie_b <= +1
 budget_limit: +2 quantity_cookie_a +2 quantity_cookie_b <= +2
bounds
bin
gen
 quantity_cookie_a
 quantity_cookie_b
semi
end
