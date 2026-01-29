from src.domain.fraud.engine import FraudEngine


def test_rule_score_flags_multiple_rules():
    labels = ["over_3sigma", "tx_1m", "device_known", "ip_suspicious", "is_night", "net_cycle", "net_mule"]
    features = [1, 5, 0, 1, 1, 1, 1]
    score, rules = FraudEngine._rule_score(features, labels)
    assert "VALUE_OVER_3SIGMA" in rules
    assert "HIGH_FREQUENCY" in rules
    assert score > 0
