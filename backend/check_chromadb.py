import chromadb

print('ChromaDB version:', chromadb.__version__)
print('\nNew client initialization examples:\n')

# Try the new client initialization method
try:
    client = chromadb.PersistentClient(path='/tmp/testdb')
    print('PersistentClient example:', client)
except Exception as e:
    print(f'Error with PersistentClient: {e}')

# Show available client types
print('\nAvailable client types:')
for item in dir(chromadb):
    if 'Client' in item:
        print(f'- {item}')