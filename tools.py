from dataclasses import dataclass
import argparse
import oci

class Types:
    OCID = str

@dataclass
class Path:
    path: str
    ocid: Types.OCID


class Var:
    old_cwd = None

class Const:
    pass

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile')
    parser.add_argument('--config')
    parser.add_argument('--auth', choices=['api_key', 'instance_obo_user', 'instance_principle', 'resource_principle', 'security_token'])
    return parser.parse_args()

def paginate(func, *args, **kwargs):
    for record in oci.pagination.list_call_get_all_results_generator(func, 'records', *args, **kwargs):
        yield record

def is_authenticated(config, signer):
    try:
        os_client = oci.object_storage.ObjectStorageClient(config, signer=signer)
        os_client.get_namespace()
    except oci.exceptions.ServiceError as e:
        return False
    return True