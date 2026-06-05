import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.application.event_handlers import EventBus
from src.application.handlers.order_handlers import register_all
from src.application.use_cases import (
    CancelOrderUseCase,
    CompleteOrderUseCase,
    CreateOrderUseCase,
    DeleteOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
)
from src.infrastructure.adapters.database import get_session
from src.infrastructure.adapters.sql_models import Base
from src.infrastructure.adapters.sql_repo import SqlOrderRepository
from src.infrastructure.api import dependencies
from src.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def session(setup_db):
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(session):
    import os

    os.environ["TESTING"] = "1"

    # Override de sesión para auth
    def override_get_session():
        yield session

    # Override de UoW para orders
    event_bus = EventBus()
    register_all(event_bus)

    class TestUnitOfWork:
        def __init__(self, s: Session):
            self.orders = SqlOrderRepository(s)
            self._session = s

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                self._session.rollback()

        def commit(self):
            self._session.commit()

        def rollback(self):
            self._session.rollback()

    def make_create_uc():
        return CreateOrderUseCase(uow=TestUnitOfWork(session), publisher=event_bus)

    def make_complete_uc():
        return CompleteOrderUseCase(uow=TestUnitOfWork(session), publisher=event_bus)

    def make_cancel_uc():
        return CancelOrderUseCase(uow=TestUnitOfWork(session), publisher=event_bus)

    def make_get_uc():
        return GetOrderUseCase(uow=TestUnitOfWork(session))

    def make_list_uc():
        return ListOrdersUseCase(uow=TestUnitOfWork(session))

    def make_delete_uc():
        return DeleteOrderUseCase(uow=TestUnitOfWork(session))

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[dependencies.get_create_order_uc] = make_create_uc
    app.dependency_overrides[dependencies.get_complete_order_uc] = make_complete_uc
    app.dependency_overrides[dependencies.get_cancel_order_uc] = make_cancel_uc
    app.dependency_overrides[dependencies.get_get_order_uc] = make_get_uc
    app.dependency_overrides[dependencies.get_list_orders_uc] = make_list_uc
    app.dependency_overrides[dependencies.get_delete_order_uc] = make_delete_uc
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "test1234",
        },
    )
    assert response.status_code == 201, f"Register failed: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


SAMPLE_ORDER = {
    "customer": "Juan",
    "items": [
        {"product": "Laptop", "price": 25000, "quantity": 1},
        {"product": "Mouse", "price": 350, "quantity": 2},
    ],
}


class TestHealthCheck:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "funcionando" in response.json()["message"]


class TestAuthFlow:
    def test_register(self, client):
        response = client.post(
            "/auth/register",
            json={
                "name": "Nuevo User",
                "email": "nuevo@example.com",
                "password": "pass1234",
            },
        )
        print(f"STATUS: {response.status_code}")
        print(f"BODY: {response.text}")
        assert response.status_code == 201
        assert "access_token" in response.json()

    def test_register_duplicate_email(self, client):
        client.post(
            "/auth/register",
            json={
                "name": "User 1",
                "email": "dup@example.com",
                "password": "pass1234",
            },
        )
        response = client.post(
            "/auth/register",
            json={
                "name": "User 2",
                "email": "dup@example.com",
                "password": "pass5678",
            },
        )
        assert response.status_code == 409

    def test_login(self, client):
        client.post(
            "/auth/register",
            json={
                "name": "Login User",
                "email": "login@example.com",
                "password": "pass1234",
            },
        )
        response = client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "pass1234",
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client):
        client.post(
            "/auth/register",
            json={
                "name": "User",
                "email": "wrong@example.com",
                "password": "correct",
            },
        )
        response = client.post(
            "/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "incorrect",
            },
        )
        assert response.status_code == 401


class TestOrdersCRUD:
    def test_create_order(self, client, auth_headers):
        response = client.post("/orders/", json=SAMPLE_ORDER, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["customer"] == "Juan"
        assert data["status"] == "pending"
        assert data["total"] == 25700
        assert len(data["items"]) == 2

    def test_create_order_without_token(self, client):
        response = client.post("/orders/", json=SAMPLE_ORDER)
        assert response.status_code in (401, 403)

    def test_create_order_invalid_data(self, client, auth_headers):
        response = client.post(
            "/orders/",
            json={"customer": "Juan", "items": []},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_list_orders_empty(self, client):
        response = client.get("/orders/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_orders_with_data(self, client, auth_headers):
        client.post("/orders/", json=SAMPLE_ORDER, headers=auth_headers)
        client.post("/orders/", json=SAMPLE_ORDER, headers=auth_headers)

        response = client.get("/orders/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_order_by_id(self, client, auth_headers):
        create_resp = client.post("/orders/", json=SAMPLE_ORDER, headers=auth_headers)
        order_id = create_resp.json()["id"]

        response = client.get(f"/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["id"] == order_id

    def test_get_order_not_found(self, client):
        response = client.get("/orders/999")
        assert response.status_code == 404

    def test_complete_order(self, client, auth_headers):
        create_resp = client.post("/orders/", json=SAMPLE_ORDER, headers=auth_headers)
        order_id = create_resp.json()["id"]

        response = client.patch(
            f"/orders/{order_id}",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_cancel_order_with_reason(self, client, auth_headers):
        create_resp = client.post("/orders/", json=SAMPLE_ORDER, headers=auth_headers)
        order_id = create_resp.json()["id"]

        response = client.patch(
            f"/orders/{order_id}",
            json={"status": "cancelled", "reason": "sin stock"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_cannot_complete_cancelled_order(self, client, auth_headers):
        create_resp = client.post("/orders/", json=SAMPLE_ORDER, headers=auth_headers)
        order_id = create_resp.json()["id"]

        client.patch(
            f"/orders/{order_id}",
            json={"status": "cancelled"},
            headers=auth_headers,
        )
        response = client.patch(
            f"/orders/{order_id}",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_delete_order(self, client, auth_headers):
        create_resp = client.post("/orders/", json=SAMPLE_ORDER, headers=auth_headers)
        order_id = create_resp.json()["id"]

        response = client.delete(f"/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 204

        get_resp = client.get(f"/orders/{order_id}")
        assert get_resp.status_code == 404
