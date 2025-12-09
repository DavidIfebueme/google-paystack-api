import uuid


def generate_transaction_reference() -> str:
    return f"TXN_{uuid.uuid4().hex}"

def kobo_to_naira(amount: int) -> float:
    return amount / 100

def naira_to_kobo(amount: float) -> int:
    return int(amount * 100)
