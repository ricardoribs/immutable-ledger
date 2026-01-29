import secrets


class SpbGateway:
    @staticmethod
    def validate_destination(bank_code: str | None, agency: str | None, account: str | None) -> bool:
        if not bank_code or not agency or not account:
            return False
        return bank_code.isdigit() and agency.isdigit() and account.isdigit()

    @staticmethod
    def calculate_fee(payment_type: str, amount: float) -> float:
        base = 2.50 if payment_type.upper() == "TED" else 3.80
        variable = 0.001 * amount
        return round(base + variable, 2)

    @staticmethod
    def send(payment_type: str) -> str:
        return f"SPB-{payment_type.upper()}-{secrets.token_hex(6)}"
