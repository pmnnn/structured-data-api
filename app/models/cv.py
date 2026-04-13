from pydantic import BaseModel, Field
from typing import Optional


class Experience(BaseModel):
    company: str = Field(description="Nom de l'entreprise")
    position: Optional[str] = Field(None, description="Intitulé du poste")
    start_date: str = Field(description="Date de début (ex: 2021-03)")
    end_date: Optional[str] = Field(None, description="Date de fin, null si poste actuel")
    description: Optional[str] = Field(None, description="Description des missions")


class Education(BaseModel):
    institution: str = Field(description="School or university name")
    degree: Optional[str] = Field(None, description="Degree or certification")
    field_of_study: Optional[str] = Field(None, description="Field of study")
    graduation_year: Optional[int] = Field(None, description="Graduation year")


class CVData(BaseModel):
    full_name: str = Field(description="Nom complet du candidat")
    email: Optional[str] = Field(None, description="Adresse email")
    phone: Optional[str] = Field(None, description="Numéro de téléphone")
    location: Optional[str] = Field(None, description="Ville / Pays")
    linkedin_url: Optional[str] = Field(None, description="URL du profil LinkedIn")
    summary: Optional[str] = Field(None, description="Résumé professionnel")
    experiences: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: Optional[list] = Field(default_factory=list)
    languages: Optional[list] = Field(default_factory=list)