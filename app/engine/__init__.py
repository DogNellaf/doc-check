"""How a contract's clauses find their reference clauses and an invoice's lines their price list.

lexical.py is ai-consultant's word overlap weighted by rarity, file for file. grams.py compares
texts by character n-grams, which survive Russian word endings. match.py pairs two lists by both,
best first, one partner each, with a "not the same thing" threshold. No model and no download:
on the examples this pairs every clause and line the same way the e5 model did, in milliseconds.
"""
