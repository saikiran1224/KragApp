import sys 
sys.path.insert(0, ".") # ensures project root is in path

# Invoking the handler 
from ingestion.handler import handler

event = {
    "file_path" : "test_doc.txt"
}

print(handler(event=event, context={}))

