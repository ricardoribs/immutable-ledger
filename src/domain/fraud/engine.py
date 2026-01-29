from datetime import datetime, timedelta
from typing import Any
import json
import ipaddress

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from src.domain.ledger import models as ledger_models
from src.domain.security import models as security_models
from src.domain.fraud import models as fraud_models
from src.domain.fraud import ml
from src.infra.metrics import FRAUD_DETECTED


class FraudEngine:
    @staticmethod
    def _is_suspicious_ip(ip: str) -> bool:
        suspicious_ranges = [
            "203.0.113.0/24",
            "198.51.100.0/24",
            "192.0.2.0/24",
        ]
        try:
            addr = ipaddress.ip_address(ip)
            for cidr in suspicious_ranges:
                if addr in ipaddress.ip_network(cidr):
                    return True
        except Exception:
            return True
        return False

    @staticmethod
    async def _device_known(db: AsyncSession, user_id: int, fingerprint: str | None) -> bool:
        if not fingerprint:
            return False
        stmt = select(security_models.Device).where(
            security_models.Device.user_id == user_id,
            security_models.Device.fingerprint == fingerprint,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none() is not None

    @staticmethod
    async def _network_signals(db: AsyncSession, account_id: int) -> dict:
        since = datetime.utcnow() - timedelta(days=7)
        stmt = select(
            ledger_models.Posting.transaction_id,
            ledger_models.Posting.account_id,
            ledger_models.Posting.amount,
        ).join(
            ledger_models.Transaction, ledger_models.Transaction.id == ledger_models.Posting.transaction_id
        ).where(
            ledger_models.Transaction.timestamp >= since,
            ledger_models.Transaction.operation_type.in_(["TRANSFER", "PIX"]),
        )
        res = await db.execute(stmt)
        rows = res.all()

        edges = {}
        tx_map = {}
        for tx_id, acc_id, amount in rows:
            tx_map.setdefault(tx_id, []).append((acc_id, amount))

        for tx_id, items in tx_map.items():
            if len(items) < 2:
                continue
            from_acc = [acc for acc, amt in items if amt < 0]
            to_acc = [acc for acc, amt in items if amt > 0]
            if from_acc and to_acc:
                edges.setdefault(from_acc[0], set()).add(to_acc[0])

        # Cycle detection (length <= 4)
        cycle_found = False
        if account_id in edges:
            for n1 in edges.get(account_id, []):
                for n2 in edges.get(n1, []):
                    for n3 in edges.get(n2, []):
                        if account_id in edges.get(n3, set()):
                            cycle_found = True
                            break
                    if cycle_found:
                        break
                if cycle_found:
                    break

        mule_score = 0
        out_degree = len(edges.get(account_id, set()))
        in_degree = sum(1 for k, v in edges.items() if account_id in v)
        if out_degree >= 5 and in_degree >= 5:
            mule_score = 1

        return {"cycle": cycle_found, "mule": mule_score}

    @staticmethod
    async def build_features(
        db: AsyncSession,
        account_id: int,
        amount_units: float,
        ip: str,
        user_agent: str,
        device_fingerprint: str | None,
    ) -> tuple[list[float], list[str]]:
        amount_value = float(amount_units)
        now = datetime.utcnow()
        hour = now.hour
        is_night = 1 if hour < 6 else 0
        weekday = now.weekday()

        stmt_acc = select(ledger_models.Account).where(ledger_models.Account.id == account_id)
        res_acc = await db.execute(stmt_acc)
        acc = res_acc.scalar_one_or_none()
        balance = float(acc.balance or 0.0) if acc else 0.0

        user_id = acc.user_id if acc else None
        stmt_user = select(ledger_models.User).where(ledger_models.User.id == user_id) if user_id else None
        if stmt_user is not None:
            res_user = await db.execute(stmt_user)
            user = res_user.scalar_one_or_none()
            account_age_days = (now - user.created_at).days if user else 0
        else:
            account_age_days = 0

        one_min = now - timedelta(minutes=1)
        ten_min = now - timedelta(minutes=10)
        one_hour = now - timedelta(hours=1)
        one_day = now - timedelta(days=1)

        stmt_tx = select(ledger_models.Transaction).where(ledger_models.Transaction.account_id == account_id)
        res_tx = await db.execute(stmt_tx)
        txs = res_tx.scalars().all()

        tx_count_1m = sum(1 for t in txs if t.timestamp >= one_min)
        tx_count_10m = sum(1 for t in txs if t.timestamp >= ten_min)
        tx_count_1h = sum(1 for t in txs if t.timestamp >= one_hour)
        tx_count_24h = sum(1 for t in txs if t.timestamp >= one_day)

        amounts_24h = [float(t.amount) for t in txs if t.timestamp >= one_day]
        avg_24h = float(sum(amounts_24h) / len(amounts_24h)) if amounts_24h else 0.0
        var_24h = float(sum((a - avg_24h) ** 2 for a in amounts_24h) / len(amounts_24h)) if amounts_24h else 0.0
        std_24h = float(var_24h ** 0.5) if var_24h else 0.0
        zscore = (amount_value - avg_24h) / (std_24h if std_24h > 0 else 1.0)

        last_tx_time = max([t.timestamp for t in txs], default=now)
        last_tx_delta = (now - last_tx_time).total_seconds()

        stmt_postings = select(
            ledger_models.Posting.transaction_id,
            ledger_models.Posting.account_id,
            ledger_models.Posting.amount,
        ).join(
            ledger_models.Transaction, ledger_models.Transaction.id == ledger_models.Posting.transaction_id
        ).where(
            ledger_models.Transaction.timestamp >= one_day,
            ledger_models.Transaction.operation_type.in_(["TRANSFER", "PIX"]),
        )
        res_post = await db.execute(stmt_postings)
        postings = res_post.all()
        tx_map = {}
        for tx_id, acc_id, amount in postings:
            tx_map.setdefault(tx_id, []).append((acc_id, amount))
        distinct_payees = set()
        for tx_id, items in tx_map.items():
            from_acc = [acc for acc, amt in items if amt < 0]
            to_acc = [acc for acc, amt in items if amt > 0]
            if from_acc and to_acc and from_acc[0] == account_id:
                distinct_payees.add(to_acc[0])
        distinct_payees_24h = len(distinct_payees)

        stmt_ips = select(security_models.Session.ip_address).where(
            security_models.Session.user_id == (user_id or 0),
            security_models.Session.created_at >= one_day,
        )
        res_ips = await db.execute(stmt_ips)
        distinct_ips_24h = len({r[0] for r in res_ips.all() if r[0]})

        device_known = await FraudEngine._device_known(db, user_id or 0, device_fingerprint)
        ip_suspicious = FraudEngine._is_suspicious_ip(ip)

        net = await FraudEngine._network_signals(db, account_id)

        features = [
            amount_value,
            abs(zscore),
            avg_24h,
            std_24h,
            tx_count_1m,
            tx_count_10m,
            tx_count_1h,
            tx_count_24h,
            balance,
            account_age_days,
            hour,
            weekday,
            is_night,
            last_tx_delta,
            1 if device_known else 0,
            1 if ip_suspicious else 0,
            1 if net["cycle"] else 0,
            net["mule"],
            len(user_agent or ""),
            distinct_payees_24h,
            distinct_ips_24h,
            1 if amount_value > avg_24h + (3 * std_24h if std_24h else 0) else 0,
            1 if amount_value > balance else 0,
            1 if account_age_days < 7 else 0,
            1 if tx_count_10m >= 10 else 0,
            1 if tx_count_1h >= 20 else 0,
            1 if amount_value > 10000 else 0,
            1 if balance <= 0 else 0,
            1 if amount_value < 1 else 0,
        ]

        labels = [
            "amount",
            "zscore",
            "avg_24h",
            "std_24h",
            "tx_1m",
            "tx_10m",
            "tx_1h",
            "tx_24h",
            "balance",
            "account_age_days",
            "hour",
            "weekday",
            "is_night",
            "last_tx_delta",
            "device_known",
            "ip_suspicious",
            "net_cycle",
            "net_mule",
            "ua_len",
            "distinct_payees_24h",
            "distinct_ips_24h",
            "over_3sigma",
            "over_balance",
            "new_account",
            "tx_10m_spike",
            "tx_1h_spike",
            "high_value_10k",
            "balance_zero",
            "dust_tx",
        ]
        return features, labels

    @staticmethod
    def _rule_score(features: list[float], labels: list[str]) -> tuple[float, list[str]]:
        rules = []
        mapping = dict(zip(labels, features))
        if mapping["over_3sigma"] == 1:
            rules.append("VALUE_OVER_3SIGMA")
        if mapping["tx_1m"] >= 3:
            rules.append("HIGH_FREQUENCY")
        if mapping["device_known"] == 0:
            rules.append("UNKNOWN_DEVICE")
        if mapping["ip_suspicious"] == 1:
            rules.append("SUSPICIOUS_IP")
        if mapping["is_night"] == 1:
            rules.append("UNUSUAL_HOUR")
        if mapping["net_cycle"] == 1:
            rules.append("SUSPECTED_CYCLE")
        if mapping["net_mule"] == 1:
            rules.append("MULE_PATTERN")
        if mapping.get("new_account", 0) == 1:
            rules.append("NEW_ACCOUNT")
        if mapping.get("tx_10m_spike", 0) == 1:
            rules.append("SPIKE_10M")
        if mapping.get("tx_1h_spike", 0) == 1:
            rules.append("SPIKE_1H")
        if mapping.get("high_value_10k", 0) == 1:
            rules.append("HIGH_VALUE")
        if mapping.get("balance_zero", 0) == 1:
            rules.append("LOW_BALANCE")
        if mapping.get("dust_tx", 0) == 1:
            rules.append("DUST_TX")

        score = min(100.0, len(rules) * 12.0 + mapping.get("zscore", 0.0) * 3.0)
        return score, rules

    @staticmethod
    async def evaluate(
        db: AsyncSession,
        account_id: int,
        amount_units: float,
        ip: str,
        user_agent: str,
        device_fingerprint: str | None,
        transaction_id: int | None = None,
    ) -> dict[str, Any]:
        stmt_acc = select(ledger_models.Account).where(ledger_models.Account.id == account_id)
        res_acc = await db.execute(stmt_acc)
        acc = res_acc.scalar_one_or_none()
        user_id = acc.user_id if acc else None

        features, labels = await FraudEngine.build_features(
            db, account_id, amount_units, ip, user_agent, device_fingerprint
        )
        rule_score, rules = FraudEngine._rule_score(features, labels)
        model_scores = ml.score_models(features)
        ml_score = min(100.0, (model_scores["iforest"] * 30.0) + (model_scores["xgb"] * 70.0))
        final_score = min(100.0, (rule_score * 0.6) + (ml_score * 0.4))

        action = "ALLOW"
        if final_score > 80:
            action = "BLOCK"
        elif final_score > 60:
            action = "VERIFY"

        record = fraud_models.FraudScore(
            account_id=account_id,
            transaction_id=transaction_id,
            score=final_score,
            action=action,
            rules=",".join(rules),
            features=json.dumps(dict(zip(labels, features))),
            model_version="v1",
        )
        db.add(record)
        await db.commit()

        FRAUD_DETECTED.labels(action=action).inc()

        if user_id and action in {"VERIFY", "BLOCK"}:
            from src.domain.security.services import SecurityService
            await SecurityService.create_alert(
                db,
                user_id,
                f"FRAUD_{action}",
                details=f"score={final_score:.2f} rules={','.join(rules)}",
            )
            from src.domain.fraud.alerts import FraudAlertService
            await FraudAlertService.alert_team(
                db,
                account_id=account_id,
                message=f"FRAUD_{action} score={final_score:.2f} rules={','.join(rules)}",
                severity="HIGH" if action == "BLOCK" else "MEDIUM",
            )
            from src.domain.notifications.services import NotificationService
            from src.domain.notifications.schemas import NotificationCreate
            await NotificationService.send(
                db,
                user_id,
                NotificationCreate(
                    channel="EMAIL",
                    subject="Alerta de fraude",
                    message=f"Detectamos atividade suspeita. Score={final_score:.2f}",
                ),
            )
            from src.domain.regulatory.services import RegulatoryService
            await RegulatoryService.create_aml_alert(
                db,
                user_id,
                rule=f"FRAUD_{action}",
                details=f"score={final_score:.2f} rules={','.join(rules)}",
            )

        if action == "BLOCK":
            raise HTTPException(
                status_code=403,
                detail="FRAUDE DETECTADA: Transacao bloqueada automaticamente.",
            )

        return {"score": final_score, "action": action, "rules": rules}
