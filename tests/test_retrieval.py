import sys
sys.path.insert(0, ".")

from retrieval.handler import handler

event = {"query": "What is the quarterly revenue?"}
result = handler(event, {})
print(result)
