"""
HoneyChain Batch Management Service
"""
from datetime import datetime, timezone
import database
from models.batch import Batch
from models.stage import StageUpdate
from utils.helpers import generate_digital_signature, generate_batch_id
from utils.validators import (
    validate_batch_id,
    validate_purity,
    validate_moisture,
    validate_hmf,
    validate_harvest_date,
)


class BatchService:
    """Orchestrates 4-stage honey supply chain lifecycle."""

    def __init__(self, blockchain_service=None, qr_service=None):
        from services.blockchain_service import BlockchainService
        from services.qr_service import QRService

        self.blockchain_service = blockchain_service or BlockchainService()
        self.qr_service = qr_service or QRService()

    def create_batch(
        self,
        product_name,
        floral_source,
        apiary_name,
        beekeeper_name,
        origin_location,
        harvest_date,
        quantity_kg,
        comb_type="Pure Capped Comb",
        extraction_method="Unheated Cold Centrifugation",
        batch_id=None,
    ):
        """Stage 1: Honey Batch Registered by Beekeeper."""
        batch_id = (batch_id or "").strip()
        if not batch_id:
            batch_id = generate_batch_id()

        if not validate_batch_id(batch_id):
            return None, "Batch ID must be 4-32 characters (letters, numbers, hyphens)."

        if database.get_batch_by_id(batch_id):
            return None, f"Batch '{batch_id}' already exists."

        if not product_name or not apiary_name or not beekeeper_name or not origin_location:
            return None, "Product name, apiary, beekeeper, and origin location are required."

        if not validate_harvest_date(harvest_date):
            return None, "Valid harvest date in YYYY-MM-DD format is required."

        try:
            qty = float(quantity_kg)
            if qty <= 0:
                return None, "Harvest quantity must be greater than zero."
        except (ValueError, TypeError):
            return None, "Invalid harvest quantity value."

        # Generate QR code
        qr_file = self.qr_service.generate_batch_qr(batch_id)

        # Mine Block 1
        block_data = {
            "product_name": product_name,
            "floral_source": floral_source,
            "apiary_name": apiary_name,
            "beekeeper_name": beekeeper_name,
            "origin_location": origin_location,
            "harvest_date": harvest_date,
            "comb_type": comb_type,
            "extraction_method": extraction_method,
            "quantity_kg": qty,
        }
        b1 = self.blockchain_service.add_batch_block(
            batch_id=batch_id,
            stage_name="Block 1: Honey Batch Registered",
            event_type="HONEY_BATCH_REGISTERED",
            details=block_data,
        )

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Save to database
        batch_record = {
            "batch_id": batch_id,
            "product_name": product_name,
            "floral_source": floral_source,
            "apiary_name": apiary_name,
            "beekeeper_name": beekeeper_name,
            "origin_location": origin_location,
            "harvest_date": harvest_date,
            "comb_type": comb_type,
            "extraction_method": extraction_method,
            "quantity_kg": qty,
            "current_stage": "Block 1: Honey Batch Registered",
            "stage_num": 1,
            "qr_code_image": qr_file,
            "tx_hash": b1.hash,
            "block_index": b1.index,
            "created_at": now_str,
        }
        database.insert_batch(batch_record)

        # Record Stage 1 in stage_updates
        database.insert_stage_update(
            batch_id=batch_id,
            stage_num=1,
            stage_name="Block 1: Honey Batch Registered",
            actor_name=beekeeper_name,
            location=origin_location,
            details=block_data,
            notes="Apiary harvest verified and registered onto blockchain ledger.",
            timestamp=now_str,
            block_hash=b1.hash,
            block_index=b1.index,
        )

        # Also register beekeeper in directory if not present
        try:
            database.insert_beekeeper_if_new(beekeeper_name, apiary_name, origin_location, floral_source)
        except Exception:
            pass

        return Batch.from_row(database.get_batch_by_id(batch_id)), None

    def record_laboratory_test(
        self,
        batch_id,
        lab_name,
        inspector_name,
        certificate_no,
        purity_score,
        moisture_content,
        hmf_level,
        nmr_profile=None,
        lab_test_date=None,
    ):
        """Stage 2: Laboratory Quality Assurance."""
        batch = database.get_batch_by_id(batch_id)
        if not batch:
            return None, f"Batch '{batch_id}' not found."

        if not lab_name or not inspector_name or not certificate_no:
            return None, "Laboratory name, inspector name, and certificate number are required."

        if not validate_purity(purity_score):
            return None, "Purity score must be between 0.0% and 100.0%."

        if not validate_moisture(moisture_content):
            return None, "Moisture content must be between 5.0% and 35.0%."

        if not validate_hmf(hmf_level):
            return None, "HMF level must be between 0.0 and 200.0 mg/kg."

        purity = float(purity_score)
        moisture = float(moisture_content)
        hmf = float(hmf_level)
        test_date = lab_test_date or datetime.now().strftime("%Y-%m-%d")

        # Cryptographic Digital Signature
        sig = generate_digital_signature(batch_id, certificate_no, purity, moisture, hmf)
        key_id = f"KEY-LAB-{lab_name.upper().replace(' ', '_')[:12]}-2026"
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Mine Block 2
        block_data = {
            "lab_name": lab_name,
            "inspector_name": inspector_name,
            "certificate_no": certificate_no,
            "purity_score": purity,
            "moisture_content": moisture,
            "hmf_level": hmf,
            "nmr_profile": nmr_profile or "100% Pure Raw Honey (NMR Verified)",
            "lab_test_date": test_date,
            "digital_signature": sig,
            "signing_key_id": key_id,
        }
        b2 = self.blockchain_service.add_batch_block(
            batch_id=batch_id,
            stage_name="Block 2: Laboratory Test Recorded",
            event_type="LAB_TEST_RECORDED",
            details=block_data,
        )

        # Update batch table
        database.update_batch_stage2(
            batch_id=batch_id,
            lab_name=lab_name,
            inspector_name=inspector_name,
            certificate_no=certificate_no,
            purity_score=purity,
            moisture_content=moisture,
            nmr_profile=nmr_profile or "100% Pure Raw Honey",
            hmf_level=hmf,
            lab_test_date=test_date,
            digital_signature=sig,
            signing_key_id=key_id,
            signature_timestamp=now_str,
            tx_hash=b2.hash,
            block_index=b2.index,
        )

        database.insert_stage_update(
            batch_id=batch_id,
            stage_num=2,
            stage_name="Block 2: Laboratory Test Recorded",
            actor_name=inspector_name,
            location=lab_name,
            details=block_data,
            notes=f"Purity: {purity}%, Moisture: {moisture}%, HMF: {hmf} mg/kg. Signature: {sig}",
            timestamp=now_str,
            block_hash=b2.hash,
            block_index=b2.index,
        )

        return Batch.from_row(database.get_batch_by_id(batch_id)), None

    def record_packaging(
        self,
        batch_id,
        packaging_plant,
        packaging_supervisor,
        jar_format,
        net_weight,
        tamper_seal_id,
        lot_number,
        packaging_date=None,
    ):
        """Stage 3: Packaging and Bottling."""
        batch = database.get_batch_by_id(batch_id)
        if not batch:
            return None, f"Batch '{batch_id}' not found."

        if not packaging_plant or not packaging_supervisor or not tamper_seal_id or not lot_number:
            return None, "Packaging plant, supervisor, tamper-seal ID, and lot number are required."

        pkg_date = packaging_date or datetime.now().strftime("%Y-%m-%d")
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Mine Block 3
        block_data = {
            "packaging_plant": packaging_plant,
            "packaging_supervisor": packaging_supervisor,
            "jar_format": jar_format or "500g Glass Hex Jar",
            "net_weight": net_weight or "500g",
            "tamper_seal_id": tamper_seal_id,
            "lot_number": lot_number,
            "packaging_date": pkg_date,
        }
        b3 = self.blockchain_service.add_batch_block(
            batch_id=batch_id,
            stage_name="Block 3: Honey Packaging Recorded",
            event_type="HONEY_PACKAGED",
            details=block_data,
        )

        # Update batch table
        database.update_batch_stage3(
            batch_id=batch_id,
            packaging_plant=packaging_plant,
            packaging_supervisor=packaging_supervisor,
            jar_format=jar_format,
            net_weight=net_weight,
            tamper_seal_id=tamper_seal_id,
            packaging_date=pkg_date,
            lot_number=lot_number,
            tx_hash=b3.hash,
            block_index=b3.index,
        )

        database.insert_stage_update(
            batch_id=batch_id,
            stage_num=3,
            stage_name="Block 3: Honey Packaging Recorded",
            actor_name=packaging_supervisor,
            location=packaging_plant,
            details=block_data,
            notes=f"Jar format: {jar_format}, Tamper Seal: {tamper_seal_id}, Lot: {lot_number}.",
            timestamp=now_str,
            block_hash=b3.hash,
            block_index=b3.index,
        )

        return Batch.from_row(database.get_batch_by_id(batch_id)), None

    def record_seller(
        self,
        batch_id,
        seller_name,
        store_location,
        license_no,
        sale_price,
        shelf_arrival_date=None,
        retail_status="On Shelf & Authenticated",
    ):
        """Stage 4: Retail & Distribution."""
        batch = database.get_batch_by_id(batch_id)
        if not batch:
            return None, f"Batch '{batch_id}' not found."

        if not seller_name or not store_location:
            return None, "Seller name and store location are required."

        arrival_date = shelf_arrival_date or datetime.now().strftime("%Y-%m-%d")
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Mine Block 4
        block_data = {
            "seller_name": seller_name,
            "store_location": store_location,
            "license_no": license_no or "N/A",
            "shelf_arrival_date": arrival_date,
            "sale_price": sale_price or "$0.00",
            "retail_status": retail_status or "On Shelf & Authenticated",
        }
        b4 = self.blockchain_service.add_batch_block(
            batch_id=batch_id,
            stage_name="Block 4: Seller Information Recorded",
            event_type="SELLER_RECORDED",
            details=block_data,
        )

        database.update_batch_stage4(
            batch_id=batch_id,
            seller_name=seller_name,
            store_location=store_location,
            license_no=license_no,
            shelf_arrival_date=arrival_date,
            sale_price=sale_price,
            retail_status=retail_status,
            tx_hash=b4.hash,
            block_index=b4.index,
        )

        database.insert_stage_update(
            batch_id=batch_id,
            stage_num=4,
            stage_name="Block 4: Seller Information Recorded",
            actor_name=seller_name,
            location=store_location,
            details=block_data,
            notes=f"Retail shelf arrival recorded at {store_location}. Price: {sale_price}.",
            timestamp=now_str,
            block_hash=b4.hash,
            block_index=b4.index,
        )

        return Batch.from_row(database.get_batch_by_id(batch_id)), None

    def get_batch(self, batch_id):
        row = database.get_batch_by_id(batch_id)
        return Batch.from_row(row) if row else None

    def get_all_batches(self):
        rows = database.get_all_batches()
        return [Batch.from_row(r) for r in rows]

    def get_batch_timeline(self, batch_id):
        rows = database.get_stage_updates_by_batch(batch_id)
        return [StageUpdate.from_row(r) for r in rows]

    def get_dashboard_counts(self):
        """Computes summary metrics for telemetry cards."""
        batches = self.get_all_batches()
        total_batches = len(batches)
        lab_tested = sum(1 for b in batches if b.stage_num >= 2)
        packaged = sum(1 for b in batches if b.stage_num >= 3)
        retail_ready = sum(1 for b in batches if b.stage_num >= 4)

        # Unique beekeepers and sellers
        beekeepers = set(b.beekeeper_name for b in batches if b.beekeeper_name)
        sellers = set(b.seller_name for b in batches if b.seller_name)

        blockchain_stats = self.blockchain_service.get_summary_stats()

        return {
            "total_batches": total_batches,
            "registered_beekeepers": len(beekeepers),
            "completed_lab_tests": lab_tested,
            "packaged_batches": packaged,
            "active_sellers": len(sellers),
            "blockchain_records": blockchain_stats["total_blocks"],
            "ledger_valid": blockchain_stats["is_valid"],
        }

