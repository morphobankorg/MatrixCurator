from langgraph.store.memory import InMemoryStore

# For now, we use a simple InMemoryStore.
# In production, this could be replaced with PostgresStore.
store = InMemoryStore()

def get_store():
    return store
