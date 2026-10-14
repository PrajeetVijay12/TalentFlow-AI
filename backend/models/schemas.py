"""Data models (the 'structured candidate data' and 'job requirement' of the pipeline)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.parsing.normalizer import (
    canonical_cert, canonical_skill, cert_key, dedupe, normalize_degree, skill_key,
)

# Project scoring from the specification.
PROJECT_SCORES = {"major": 100, "college_major": 80, "mini": 60}
PROJECT_LABELS = {"major": "Major Project", "college_major": "College Major Project", "mini": "Mini Project"}


class Project(BaseModel):
    name: str
    category: str = "mini"  # major | college_major | mini
    score: int = 60
    evidence: str = ""  # why this category was chosen (explainability)


class CandidateProfile(BaseModel):
    id: Optional[int] = None
    filename: str = ""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    degree: Optional[str] = None
    cgpa: Optional[float] = None
    skills: list[str] = Field(default_factory=list)
    experience: float = 0.0  # years
    location: Optional[str] = None
    projects: list[Project] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)  # how each field was extracted


class Weights(BaseModel):
    skills: float = 0.4
    experience: float = 0.3
    projects: float = 0.2
    certifications: float = 0.1

    @model_validator(mode="after")
    def _check(self):
        vals = [self.skills, self.experience, self.projects, self.certifications]
        if any(v < 0 for v in vals):
            raise ValueError("Weights cannot be negative.")
        if sum(vals) <= 0:
            raise ValueError("At least one weight must be greater than zero.")
        return self

    def normalized(self) -> "Weights":
        s = self.skills + self.experience + self.projects + self.certifications
        return Weights(skills=self.skills / s, experience=self.experience / s,
                       projects=self.projects / s, certifications=self.certifications / s)


class Thresholds(BaseModel):
    selected: float = 85.0
    waitlist: float = 70.0

    @model_validator(mode="after")
    def _check(self):
        if not (0 <= self.waitlist <= 100 and 0 <= self.selected <= 100):
            raise ValueError("Thresholds must be between 0 and 100.")
        if self.selected < self.waitlist:
            raise ValueError("The 'Selected' threshold must be >= the 'Wait List' threshold.")
        return self


class JobRequirements(BaseModel):
    title: str = "Software Engineer"
    required_degrees: list[str] = Field(default_factory=lambda: ["B.Tech"])
    degrees_equivalent: bool = True  # treat B.E. = B.Tech and M.E. = M.Tech
    min_cgpa: float = 7.5
    min_experience: float = 1.0
    required_skills: list[str] = Field(default_factory=lambda: ["Python", "Java", "SQL"])
    required_certifications: list[str] = Field(default_factory=lambda: ["AWS"])
    certifications_mandatory: bool = False
    skills_mandatory: bool = True
    location: Optional[str] = None  # when set, candidate location must match (hard constraint)
    openings: int = 2  # how many candidates Alpha-Beta may select
    weights: Weights = Field(default_factory=Weights)
    thresholds: Thresholds = Field(default_factory=Thresholds)

    @field_validator("title")
    @classmethod
    def _title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Job title is required.")
        return v

    @field_validator("min_cgpa")
    @classmethod
    def _cgpa(cls, v: float) -> float:
        if not 0 <= v <= 10:
            raise ValueError("Minimum CGPA must be between 0 and 10.")
        return v

    @field_validator("min_experience")
    @classmethod
    def _exp(cls, v: float) -> float:
        if v < 0 or v > 50:
            raise ValueError("Minimum experience must be between 0 and 50 years.")
        return v

    @field_validator("openings")
    @classmethod
    def _open(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("Number of openings must be between 1 and 100.")
        return v

    @field_validator("location")
    @classmethod
    def _loc(cls, v):
        v = (v or "").strip()
        return v or None

    @model_validator(mode="after")
    def _normalize(self):
        self.required_degrees = dedupe([normalize_degree(d) for d in self.required_degrees if d.strip()],
                                       lambda d: d.lower())
        self.required_skills = dedupe([canonical_skill(s) for s in self.required_skills if s.strip()], skill_key)
        self.required_certifications = dedupe(
            [canonical_cert(c) for c in self.required_certifications if c.strip()], cert_key)
        if not self.required_skills:
            raise ValueError("Add at least one required skill.")
        return self
