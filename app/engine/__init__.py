"""The search core of ai-consultant v0.3.1 (github.com/DogNellaf/ai-consultant), file for file.

embed.py runs multilingual-e5-small (int8 ONNX) on the CPU, lexical.py weighs the shared words by
rarity; a pair is scored the same way as in ai-consultant's search.py: meaning plus 0.1 of the
word overlap. Here the core matches a contract's clauses to the company's reference contract and
an invoice's lines to the agreed price list, instead of questions to a knowledge base.
"""
