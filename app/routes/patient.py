import uuid
from datetime import timezone
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from nuvie_db.nuvie.models.patient import (
    Patient,
    PatientCreate,
    PatientUpdate,
    PatientPublic,
    PatientPublicWithDetails,
    PatientsPublic,
)

from app.core.db import async_session
from app.core.deps import CurrentUser

router = APIRouter()


def to_naive(dt):
    if dt and dt.tzinfo:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


@router.post('/', response_model=PatientPublic)
async def create_patient(
    *,
    current_user: CurrentUser,
    patient_in: PatientCreate,
) -> Any:
    """
    Criar um novo paciente.
    """
    async with async_session() as session:
        result = await session.exec(
            select(Patient).where(Patient.SSN == patient_in.SSN)
        )
        existing_patient = result.first()

        if existing_patient:
            raise HTTPException(
                status_code=400,
                detail='Já existe um paciente cadastrado com este CPF/SSN',
            )

        if patient_in.birth_date:
            patient_in.birth_date = to_naive(patient_in.birth_date)
        if patient_in.death_date:
            patient_in.death_date = to_naive(patient_in.death_date)

        db_patient = Patient.model_validate(patient_in.model_dump())
        db_patient.id = str(uuid.uuid4())
        session.add(db_patient)
        await session.commit()
        await session.refresh(db_patient)

        return db_patient


@router.get('/', response_model=PatientsPublic)
async def read_patients(
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = Query(default=100, le=100),
) -> Any:
    """
    Recuperar lista de pacientes com paginação.
    """
    async with async_session() as session:
        count_result = await session.exec(select(Patient))
        count = len(count_result.all())

        result = await session.exec(select(Patient).offset(skip).limit(limit))
        patients = result.all()

        return PatientsPublic(data=patients, count=count)


@router.get('/{patient_id}', response_model=PatientPublicWithDetails)
async def read_patient(
    patient_id: str,
    current_user: CurrentUser,
) -> Any:
    """
    Recuperar um paciente específico por ID.
    """
    async with async_session() as session:
        patient = await session.get(Patient, patient_id)
        if not patient:
            raise HTTPException(
                status_code=404, detail='Paciente não encontrado'
            )
        return patient


@router.put('/{patient_id}', response_model=PatientPublic)
async def update_patient(
    *,
    current_user: CurrentUser,
    patient_id: str,
    patient_in: PatientUpdate,
) -> Any:
    """
    Atualizar um paciente existente.
    """
    async with async_session() as session:
        patient = await session.get(Patient, patient_id)
        if not patient:
            raise HTTPException(
                status_code=404, detail='Paciente não encontrado'
            )

        if patient_in.SSN and patient_in.SSN != patient.SSN:
            result = await session.exec(
                select(Patient).where(
                    Patient.SSN == patient_in.SSN, Patient.id != patient_id
                )
            )
            existing_patient = result.first()

            if existing_patient:
                raise HTTPException(
                    status_code=400,
                    detail='Já existe outro paciente cadastrado com este CPF/SSN',
                )

        patient_data = patient_in.model_dump(exclude_unset=True)
        for field, value in patient_data.items():
            setattr(patient, field, value)

        session.add(patient)
        await session.commit()
        await session.refresh(patient)

        return patient


@router.delete('/{patient_id}')
async def delete_patient(
    patient_id: str,
    current_user: CurrentUser,
) -> Any:
    """
    Deletar um paciente.
    """
    async with async_session() as session:
        patient = await session.get(Patient, patient_id)
        if not patient:
            raise HTTPException(
                status_code=404, detail='Paciente não encontrado'
            )

        await session.delete(patient)
        await session.commit()

        return {'message': 'Paciente deletado com sucesso'}


@router.get('/search/by-ssn/{ssn}', response_model=PatientPublicWithDetails)
async def search_patient_by_ssn(
    ssn: str,
    current_user: CurrentUser,
) -> Any:
    """
    Buscar paciente por SSN.
    """
    async with async_session() as session:
        result = await session.exec(select(Patient).where(Patient.SSN == ssn))
        patient = result.first()

        if not patient:
            raise HTTPException(
                status_code=404,
                detail='Paciente não encontrado com este CPF/SSN',
            )

        return patient


@router.get('/search/by-name/{name}', response_model=PatientsPublic)
async def search_patients_by_name(
    name: str,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = Query(default=100, le=100),
) -> Any:
    """
    Buscar pacientes por nome (busca parcial).
    """
    async with async_session() as session:
        result = await session.exec(
            select(Patient)
            .where(Patient.full_name.ilike(f'%{name}%'))
            .offset(skip)
            .limit(limit)
        )
        patients = result.all()

        count_result = await session.exec(
            select(Patient).where(Patient.full_name.ilike(f'%{name}%'))
        )
        count = len(count_result.all())

        return PatientsPublic(data=patients, count=count)


@router.get('/{patient_id}/basic-data')
async def get_patient_basic_data(
    patient_id: str,
    current_user: CurrentUser,
) -> Any:
    """
    Recuperar dados básicos formatados do paciente.
    """
    async with async_session() as session:
        patient = await session.get(Patient, patient_id)
        if not patient:
            raise HTTPException(
                status_code=404, detail='Paciente não encontrado'
            )

        return {
            'patient_id': patient.id,
            'basic_data': patient.patient_basic_data,
        }
