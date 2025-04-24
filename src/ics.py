import isaac_sas
from fastapi import HTTPException
from lib.ics_components.src.models.coder import Coder


def list() -> list[Coder]:
    coder_ids = isaac_sas.fetch_stored_models()
    return [Coder(id=model_id, label=model_id) for model_id in coder_ids]

def delete(coder_id: str) -> None:
    try:
        isaac_sas.delete_model(coder_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Coder id {coder_id} not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Could not delete file of {coder_id}")