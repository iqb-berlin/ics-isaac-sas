import isaac_sas.instructions as instructions
from models.service_info import ServiceInfo

def get_info() -> ServiceInfo:
    return ServiceInfo(
        id = 'server ID',  # TODO
        type = 'issac-sas-coding-service',
        version = '0.0.2', # TODO
        apiVersion = '0.0.2',
        instructionsSchema = instructions.get_schema()
    )


