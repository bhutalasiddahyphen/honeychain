"""
HoneyChain Honey Batch Model
"""
from datetime import datetime, timezone


class Batch:
    """Represents a honey batch moving through the 4-stage supply chain."""

    STAGES = [
        "Block 1: Honey Batch Registered",
        "Block 2: Laboratory Test Recorded",
        "Block 3: Honey Packaging Recorded",
        "Block 4: Seller Information Recorded",
    ]

    def __init__(
        self,
        batch_id,
        product_name,
        floral_source,
        apiary_name,
        beekeeper_name,
        origin_location,
        harvest_date,
        comb_type="Pure Capped Comb",
        extraction_method="Unheated Cold Centrifugation",
        quantity_kg=0.0,
        current_stage="Block 1: Honey Batch Registered",
        stage_num=1,
        qr_code_image="",
        tx_hash="",
        block_index=1,
        created_at=None,
        # Lab testing
        lab_name=None,
        inspector_name=None,
        certificate_no=None,
        purity_score=None,
        moisture_content=None,
        nmr_profile=None,
        hmf_level=None,
        lab_test_date=None,
        digital_signature=None,
        signing_key_id=None,
        signature_timestamp=None,
        # Packaging
        packaging_plant=None,
        packaging_supervisor=None,
        jar_format=None,
        net_weight=None,
        tamper_seal_id=None,
        packaging_date=None,
        lot_number=None,
        # Seller
        seller_name=None,
        store_location=None,
        license_no=None,
        shelf_arrival_date=None,
        sale_price=None,
        retail_status="On Shelf & Authenticated",
    ):
        self.batch_id = batch_id
        self.product_name = product_name
        self.floral_source = floral_source
        self.apiary_name = apiary_name
        self.beekeeper_name = beekeeper_name
        self.origin_location = origin_location
        self.harvest_date = harvest_date
        self.comb_type = comb_type
        self.extraction_method = extraction_method
        self.quantity_kg = float(quantity_kg or 0.0)
        self.current_stage = current_stage
        self.stage_num = int(stage_num or 1)
        self.qr_code_image = qr_code_image
        self.tx_hash = tx_hash
        self.block_index = block_index
        self.created_at = created_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Stage 2: Lab
        self.lab_name = lab_name
        self.inspector_name = inspector_name
        self.certificate_no = certificate_no
        self.purity_score = float(purity_score) if purity_score is not None and purity_score != "" else None
        self.moisture_content = float(moisture_content) if moisture_content is not None and moisture_content != "" else None
        self.nmr_profile = nmr_profile
        self.hmf_level = float(hmf_level) if hmf_level is not None and hmf_level != "" else None
        self.lab_test_date = lab_test_date
        self.digital_signature = digital_signature
        self.signing_key_id = signing_key_id
        self.signature_timestamp = signature_timestamp

        # Stage 3: Packaging
        self.packaging_plant = packaging_plant
        self.packaging_supervisor = packaging_supervisor
        self.jar_format = jar_format
        self.net_weight = net_weight
        self.tamper_seal_id = tamper_seal_id
        self.packaging_date = packaging_date
        self.lot_number = lot_number

        # Stage 4: Seller
        self.seller_name = seller_name
        self.store_location = store_location
        self.license_no = license_no
        self.shelf_arrival_date = shelf_arrival_date
        self.sale_price = sale_price
        self.retail_status = retail_status

    def to_dict(self):
        return {
            "batch_id": self.batch_id,
            "product_name": self.product_name,
            "floral_source": self.floral_source,
            "apiary_name": self.apiary_name,
            "beekeeper_name": self.beekeeper_name,
            "origin_location": self.origin_location,
            "harvest_date": self.harvest_date,
            "comb_type": self.comb_type,
            "extraction_method": self.extraction_method,
            "quantity_kg": self.quantity_kg,
            "current_stage": self.current_stage,
            "stage_num": self.stage_num,
            "qr_code_image": self.qr_code_image,
            "tx_hash": self.tx_hash,
            "block_index": self.block_index,
            "created_at": self.created_at,
            "lab_name": self.lab_name,
            "inspector_name": self.inspector_name,
            "certificate_no": self.certificate_no,
            "purity_score": self.purity_score,
            "moisture_content": self.moisture_content,
            "nmr_profile": self.nmr_profile,
            "hmf_level": self.hmf_level,
            "lab_test_date": self.lab_test_date,
            "digital_signature": self.digital_signature,
            "signing_key_id": self.signing_key_id,
            "signature_timestamp": self.signature_timestamp,
            "packaging_plant": self.packaging_plant,
            "packaging_supervisor": self.packaging_supervisor,
            "jar_format": self.jar_format,
            "net_weight": self.net_weight,
            "tamper_seal_id": self.tamper_seal_id,
            "packaging_date": self.packaging_date,
            "lot_number": self.lot_number,
            "seller_name": self.seller_name,
            "store_location": self.store_location,
            "license_no": self.license_no,
            "shelf_arrival_date": self.shelf_arrival_date,
            "sale_price": self.sale_price,
            "retail_status": self.retail_status,
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        d = dict(row)
        return cls(**{k: d[k] for k in d if k in cls.__init__.__code__.co_varnames})

