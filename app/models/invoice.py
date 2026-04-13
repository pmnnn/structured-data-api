from pydantic import BaseModel, Field
from typing import Optional


class InvoiceLineItem(BaseModel):
    description: str = Field(description="Description du produit ou service")
    quantity: float = Field(description="Quantité")
    unit_price: float = Field(description="Prix unitaire HT")
    total_ht: float = Field(description="Total ligne HT")
    vat_rate: Optional[float] = Field(None, description="Taux de TVA en %")


class InvoiceData(BaseModel):
    invoice_number: str = Field(description="Numéro de facture")
    invoice_date: str = Field(description="Date de facturation (ISO 8601)")
    due_date: Optional[str] = Field(None, description="Date d'échéance")
    currency: str = Field(default="EUR", description="Code devise ISO")

    seller_name: str = Field(description="Nom du vendeur")
    seller_address: Optional[str] = Field(None, description="Adresse du vendeur")
    seller_vat_number: Optional[str] = Field(None, description="Numéro de TVA")

    buyer_name: str = Field(description="Nom de l'acheteur")
    buyer_address: Optional[str] = Field(None, description="Adresse de facturation")

    line_items: list[InvoiceLineItem] = Field(default_factory=list)

    total_ht: float = Field(description="Total hors taxes")
    total_vat: Optional[float] = Field(None, description="Montant total de TVA")
    total_ttc: float = Field(description="Total toutes taxes comprises")
    payment_method: Optional[str] = Field(None, description="Mode de paiement")
    notes: Optional[str] = Field(None, description="Mentions légales ou remarques")