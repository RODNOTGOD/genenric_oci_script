import oci
import os
from collections import ChainMap

USER_DEFAULTS = {
    'profile': oci.config.DEFAULT_PROFILE,
    'config': oci.config.DEFAULT_LOCATION,
    'auth': 'api_key',
}

ENV_DEFAULTS = {
    'profile': os.environ.get('OCI_CLI_PROFILE') or None,
    'config': os.environ.get('OCI_CLI_CONFIG_FILE') or None,
    'auth': os.environ.get('OCI_CLI_AUTH') or None,
}

def create_signer_from_token(config_path, profile):
    config = oci.config.from_file(config_path, profile)
    token_file = config.get('security_token_file')
    if token_file is None:
        raise oci.exceptions.InvalidConfig(f'Missing "security_token_file" within config at {config_path}')
    token = None
    with open(token_file) as f:
        token = f.read()
    priv_key = oci.signer.load_private_key_from_file(config['key_file'])
    signer = oci.auth.signers.SecurityTokenSigner(token, priv_key)
    return config, signer

def create_config_and_signer(args):
    cmdline_args = {k: v for k, v in vars(args).items() if v is not None}
    env_defaults = {k: v for k, v in ENV_DEFAULTS.items() if v is not None}
    user_auth = ChainMap(cmdline_args, env_defaults, USER_DEFAULTS)
    match user_auth['auth']:
        case 'api_key':
            config = oci.config.from_file(user_auth['config'], user_auth['profile'])
            signer = oci.signer.Signer(tenancy=config["tenancy"], user=config["user"], fingerprint=config["fingerprint"], private_key_file_location=config.get("key_file"),
                                       pass_phrase=oci.config.get_config_value_or_default(config, "pass_phrase"), private_key_content=config.get("key_content"))
        case 'instance_obo_user':
            config, signer = create_signer_from_token(user_auth['config'], user_auth['profile'])
        case 'instance_principle':
            config = oci.config.DEFAULT_CONFIG
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        case 'resource_principle':
            config = oci.config.DEFAULT_CONFIG
            signer = oci.auth.signers.get_resource_principals_signer()
        case 'security_token':
            config, signer = create_signer_from_token(user_auth['config'], user_auth['profile'])
        case _:
            raise AssertionError('Invalid authencation method reached')
    return {'config': config, 'signer': signer, 'type': user_auth['auth'], 'file': user_auth['config'], 'profile': user_auth['profile']}