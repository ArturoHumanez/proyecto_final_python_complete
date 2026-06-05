import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.domain.entities import Order, OrderItem
from src.infrastructure.adapters.memory_repo import InMemoryOrderRepository
from src.infrastructure.adapters.sql_models import Base
from src.infrastructure.adapters.sql_repo import SqlOrderRepository

SAMPLE_ITEMS = [
    OrderItem(product="Laptop", price=25000, quantity=1),
    OrderItem(product="Mouse", price=350, quantity=2),
]


@pytest.fixture
def memory_repo():
    return InMemoryOrderRepository()


@pytest.fixture
def sql_repo():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield SqlOrderRepository(session)
    session.close()


@pytest.fixture(params=["memory", "sql"])
def repo(request, memory_repo, sql_repo):
    if request.param == "memory":
        return memory_repo
    return sql_repo


class TestRepositoryContract:
    """El mismo test pasa con ambos repos — eso es el contrato."""

    def test_save_assigns_id(self, repo):
        order = Order(customer="Juan", items=SAMPLE_ITEMS)
        saved = repo.save(order)
        assert saved.id is not None

    def test_find_by_id(self, repo):
        order = Order(customer="Juan", items=SAMPLE_ITEMS)
        saved = repo.save(order)

        found = repo.find_by_id(saved.id)
        assert found is not None
        assert found.customer == "Juan"
        assert found.total == 25700

    def test_find_by_id_not_found(self, repo):
        result = repo.find_by_id(999)
        assert result is None

    def test_find_all(self, repo):
        repo.save(Order(customer="Juan", items=SAMPLE_ITEMS))
        repo.save(Order(customer="María", items=SAMPLE_ITEMS))

        all_orders = repo.find_all()
        assert len(all_orders) == 2

    def test_find_by_status(self, repo):
        order1 = Order(customer="Juan", items=SAMPLE_ITEMS)
        order2 = Order(customer="María", items=SAMPLE_ITEMS)
        order1 = repo.save(order1)
        repo.save(order2)

        order1.status = "completed"
        repo.save(order1)

        completed = repo.find_by_status("completed")
        pending = repo.find_by_status("pending")

        assert len(completed) == 1
        assert len(pending) == 1

    def test_delete(self, repo):
        order = Order(customer="Juan", items=SAMPLE_ITEMS)
        saved = repo.save(order)

        result = repo.delete(saved.id)
        assert result is True
        assert repo.find_by_id(saved.id) is None

    def test_delete_not_found(self, repo):
        result = repo.delete(999)
        assert result is False
