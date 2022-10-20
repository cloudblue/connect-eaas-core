def obfuscate_header(key, value):
    if key in ('authorization', 'authentication'):
        if value.startswith('ApiKey '):
            return value.split(':')[0] + ':' + '*' * 10
        else:
            return '*' * 20
    if key in ('cookie', 'set-cookie') and 'api_key="' in value:
        start_idx = value.index('api_key="') + len('api_key="')
        end_idx = value.index('"', start_idx)
        return f'{value[0:start_idx + 2]}******{value[end_idx - 2:]}'
    return value
