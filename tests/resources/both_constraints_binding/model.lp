\ File written by HiGHS .lp file handler
max
 obj: +30 quantity_x_item +25 quantity_y_item 
st
 weight_limit: +1 quantity_x_item +2 quantity_y_item <= +6
 budget_limit: +2 quantity_x_item +1 quantity_y_item <= +9
bounds
bin
gen
 quantity_x_item
 quantity_y_item
semi
end
