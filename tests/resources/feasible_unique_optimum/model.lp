\ File written by HiGHS .lp file handler
max
 obj: +200 quantity_protein_bar +150 quantity_chips +140 quantity_soda 
st
 weight_limit: +2 quantity_protein_bar +1 quantity_chips +3 quantity_soda <= +5
 budget_limit: +4 quantity_protein_bar +3 quantity_chips +6 quantity_soda <= +10
bounds
bin
gen
 quantity_protein_bar
 quantity_chips
 quantity_soda
semi
end
