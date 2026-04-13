from pydantic import BaseModel, Field
from typing import Optional


class QuoteLineItem(BaseModel):
    description: str = Field(description="Description du produit ou service")
    quantity: float = Field(description="Quantité estimée")
    unit_price: float = Field(description="Prix unitaire HT")
    total_ht: float = Field(description="Total ligne HT")
    discount_percent: Optional[float] = Field(None, description="Remise en %")


class QuoteData(BaseModel):
    quote_number: str = Field(description="Numéro de devis")
    quote_date: str = Field(description="Date d'émission (ISO 8601)")
    valid_until: Optional[str] = Field(None, description="Date de validité")
    currency: str = Field(default="EUR", description="Code devise ISO")

    seller_name: str = Field(description="Nom du prestataire")
    seller_address: Optional[str] = Field(None, description="Adresse du prestataire")
    seller_email: Optional[str] = Field(None, description="Email de contact")
    seller_phone: Optional[str] = Field(None, description="Téléphone de contact")

    client_name: str = Field(description="Nom du client")
    client_address: Optional[str] = Field(None, description="Adresse du client")

    line_items: list[QuoteLineItem] = Field(default_factory=list)

    total_ht: float = Field(description="Total hors taxes")
    discount_total: Optional[float] = Field(None, description="Remise globale en euros")
    total_vat: Optional[float] = Field(None, description="Total TVA")
    total_ttc: float = Field(description="Total TTC")

    payment_terms: Optional[str] = Field(None, description="Conditions de paiement")
    delivery_delay: Optional[str] = Field(None, description="Délai de livraison")
    notes: Optional[str] = Field(None, description="Conditions générales ou remarques")