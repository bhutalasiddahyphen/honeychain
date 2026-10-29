"""
HoneyChain Batch Management Unit & Integration Tests
"""
import pytest
from app import app
from services.batch_service import BatchService
import database


@pytest.fixture
def batch_service():
    return BatchService()


def test_batch_lifecycle_full_flow(batch_service):
    # Unique test batch ID
    import random
    test_id = f"TEST-HC-{random.randint(10000, 99999)}"

    # Stage 1: Create Batch
    batch, err = batch_service.create_batch(
        product_name="Alpine Gold Test Honey",
        floral_source="Wild Alpine Blossom",
        apiary_name="Test High Apiary",
        beekeeper_name="Test Beekeeper",
        origin_location="Valais, Switzerland",
        harvest_date="2026-08-15",
        quantity_kg=150.0,
        batch_id=test_id
    )
    assert err is None
    assert batch is not None
    assert batch.batch_id == test_id
    assert batch.stage_num == 1

    # Stage 2: Laboratory Test
    batch, err = batch_service.record_laboratory_test(
        batch_id=test_id,
        lab_name="Swiss Test Quality Lab",
        inspector_name="Dr. Tester",
        certificate_no="CERT-TEST-99",
        purity_score=99.6,
        moisture_content=16.2,
        hmf_level=3.8
    )
    assert err is None
    assert batch.stage_num == 2
    assert batch.purity_score == 99.6
    assert batch.digital_signature is not None

    # Stage 3: Packaging
    batch, err = batch_service.record_packaging(
        batch_id=test_id,
        packaging_plant="Test Bottling Plant",
        packaging_supervisor="Test Supervisor",
        jar_format="500g Hex Jar",
        net_weight="500g",
        tamper_seal_id=f"SEAL-{test_id}",
        lot_number=f"LOT-{test_id}"
    )
    assert err is None
    assert batch.stage_num == 3
    assert batch.tamper_seal_id == f"SEAL-{test_id}"

    # Stage 4: Seller
    batch, err = batch_service.record_seller(
        batch_id=test_id,
        seller_name="Test Organic Store",
        store_location="Zurich, Switzerland",
        license_no="ZH-TEST-01",
        sale_price="$28.00"
    )
    assert err is None
    assert batch.stage_num == 4
    assert batch.seller_name == "Test Organic Store"


def test_batch_validation_invalid_purity(batch_service):
    import random
    test_id = f"TEST-INV-{random.randint(10000, 99999)}"
    batch_service.create_batch(
        product_name="Test Honey",
        floral_source="Acacia",
        apiary_name="Apiary",
        beekeeper_name="Keeper",
        origin_location="Location",
        harvest_date="2026-08-15",
        quantity_kg=50.0,
        batch_id=test_id
    )

    # Invalid purity score > 100%
    _, err = batch_service.record_laboratory_test(
        batch_id=test_id,
        lab_name="Lab",
        inspector_name="Inspector",
        certificate_no="CERT",
        purity_score=150.0,
        moisture_content=17.0,
        hmf_level=5.0
    )
    assert err is not None
    assert "Purity score must be between 0.0% and 100.0%" in err

