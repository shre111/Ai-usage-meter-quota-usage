import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.mock import MockProvider
from app.db import Base
from app.repositories import get_quota, upsert_quota
from app.services.metering import GenerationService
from app.services.quota import QuotaExceeded


def test_near_simultaneous_requests_do_not_overspend(tmp_path):
    db_path = tmp_path / "concurrency.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    setup = Session()
    upsert_quota(setup, "racer", monthly_allowance=10, multiplier=1.0)
    setup.close()

    n = 5
    barrier = threading.Barrier(n)
    results = {"success": 0, "rejected": 0}
    lock = threading.Lock()

    def worker():
        barrier.wait()
        session = Session()
        try:
            GenerationService(session, MockProvider()).generate(
                "racer", "hi", max_tokens=100
            )
            with lock:
                results["success"] += 1
        except QuotaExceeded:
            with lock:
                results["rejected"] += 1
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    check = Session()
    quota = get_quota(check, "racer")
    used, reserved, allowance = (
        quota.used_credits,
        quota.reserved_credits,
        quota.monthly_allowance,
    )
    check.close()
    engine.dispose()

    assert results["success"] == 2
    assert results["rejected"] == 3
    assert reserved == 0
    assert used <= allowance
