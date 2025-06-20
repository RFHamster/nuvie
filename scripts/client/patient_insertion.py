import asyncio
import pandas as pd
from datetime import datetime
from typing import Optional
from sqlmodel import select
from nuvie_db.nuvie.models.patient import Patient, PatientCreate

from app.core.db import async_session
from app.core.logger import log as logger


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Converte string de data para datetime.
    Assume formato YYYY-MM-DD ou similar.
    """
    if not date_str or pd.isna(date_str) or date_str.strip() == '':
        return None

    try:
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue

        return pd.to_datetime(date_str)

    except Exception as e:
        logger.warning(f"Erro ao converter data '{date_str}': {e}")
        return None


def clean_string(value) -> Optional[str]:
    """
    Limpa e valida strings.
    """
    if pd.isna(value) or value == '' or str(value).strip() == '':
        return None
    return str(value).strip()


def clean_float(value) -> Optional[float]:
    """
    Limpa e valida valores float.
    """
    if pd.isna(value) or value == '' or str(value).strip() == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def map_csv_to_patient(row) -> PatientCreate:
    """
    Mapeia uma linha do CSV para um objeto PatientCreate.
    """
    first_name = clean_string(row.get('FIRST', ''))
    middle_name = clean_string(row.get('MIDDLE', ''))
    last_name = clean_string(row.get('LAST', ''))
    prefix = clean_string(row.get('PREFIX', ''))
    suffix = clean_string(row.get('SUFFIX', ''))

    name_parts = []
    if prefix:
        name_parts.append(prefix)
    if first_name:
        name_parts.append(first_name)
    if middle_name:
        name_parts.append(middle_name)
    if last_name:
        name_parts.append(last_name)
    if suffix:
        name_parts.append(suffix)

    full_name = ' '.join(name_parts) if name_parts else None

    marital_mapping = {
        'S': 'Solteiro',
        'M': 'Casado',
        'D': 'Divorciado',
        'W': 'Viúvo',
        'SINGLE': 'Solteiro',
        'MARRIED': 'Casado',
        'DIVORCED': 'Divorciado',
        'WIDOWED': 'Viúvo'
    }

    marital_status = clean_string(row.get('MARITAL'))
    civil_state = None
    if marital_status:
        civil_state = marital_mapping.get(marital_status.upper(), marital_status)

    gender_mapping = {
        'M': 'Masculino',
        'F': 'Feminino',
        'MALE': 'Masculino',
        'FEMALE': 'Feminino'
    }

    gender_raw = clean_string(row.get('GENDER'))
    gender = None
    if gender_raw:
        gender = gender_mapping.get(gender_raw.upper(), gender_raw)

    race_mapping = {
        'WHITE': 'Branco',
        'BLACK': 'Preto',
        'HISPANIC': 'Pardo',
        'ASIAN': 'Amarelo',
        'NATIVE': 'Indígena',
        'OTHER': 'Outro'
    }

    race_raw = clean_string(row.get('RACE'))
    race = None
    if race_raw:
        race = race_mapping.get(race_raw.upper(), race_raw)

    return PatientCreate(
        birth_date=parse_date(row.get('BIRTHDATE')),
        death_date=parse_date(row.get('DEATHDATE')),
        SSN=clean_string(row.get('SSN')),
        full_name=full_name,
        gender=gender,
        self_declared_color=race,
        civil_state=civil_state,
        income=clean_float(row.get('INCOME')),
        address=clean_string(row.get('ADDRESS')),
        city=clean_string(row.get('CITY')),
        state=clean_string(row.get('STATE')),
        zip_code=clean_string(row.get('ZIP')),
        healthcare_coverage=clean_string(row.get('HEALTHCARE_COVERAGE'))
    )


async def import_patients_from_csv(csv_file_path: str, batch_size: int = 100):
    """
    Importa pacientes do CSV para o banco de dados.
    """
    try:
        logger.info(f"Lendo arquivo CSV: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        logger.info(f"Total de linhas no CSV: {len(df)}")

        success_count = 0
        error_count = 0
        duplicate_count = 0

        for start_idx in range(0, len(df), batch_size):
            end_idx = min(start_idx + batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]

            logger.info(f"Processando lote {start_idx // batch_size + 1}: linhas {start_idx + 1} a {end_idx}")

            async with async_session() as session:
                for idx, row in batch_df.iterrows():
                    try:
                        if pd.isna(row.get('SSN')) or pd.isna(row.get('BIRTHDATE')):
                            logger.warning(f"Linha {idx + 1}: SSN ou BIRTHDATE ausente, pulando...")
                            error_count += 1
                            continue

                        existing_patient = await session.exec(
                            select(Patient).where(Patient.SSN == str(row.get('SSN')))
                        )
                        if existing_patient.first():
                            logger.info(f"Linha {idx + 1}: Paciente com SSN {row.get('SSN')} já existe, pulando...")
                            duplicate_count += 1
                            continue

                        patient_data = map_csv_to_patient(row)

                        db_patient = Patient(
                            id=clean_string(row.get('Id')),
                            **patient_data.model_dump()
                        )

                        session.add(db_patient)
                        success_count += 1

                    except Exception as e:
                        logger.error(f"Erro ao processar linha {idx + 1}: {e}")
                        error_count += 1
                        continue

                try:
                    await session.commit()
                    logger.info(f"Lote commitado com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao commitar lote: {e}")
                    await session.rollback()

        logger.info(f"""
        === RESUMO DA IMPORTAÇÃO ===
        Total de registros processados: {len(df)}
        Sucessos: {success_count}
        Erros: {error_count}
        Duplicados (pulados): {duplicate_count}
        ===========================
        """)

    except Exception as e:
        logger.error(f"Erro geral na importação: {e}")
        raise


async def main():
    """
    Função principal para executar a importação.
    """
    csv_file_path = "patients.csv"

    try:
        await import_patients_from_csv(csv_file_path, batch_size=50)
        print("Importação concluída com sucesso!")

    except Exception as e:
        print(f"Erro na importação: {e}")


if __name__ == "__main__":
    asyncio.run(main())