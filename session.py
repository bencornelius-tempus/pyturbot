"""
"""
from pathlib import Path
import json
import os
import logging
import yaml
import requests
from requests.auth import HTTPBasicAuth 

# Configure default logger to do nothing
log = logging.getLogger('turbot-python')

class Session(object):
    """
    """
    def __init__(
        self,
        *args,
        **kwargs):
        self.configure(args[0])
        self.host = kwargs["host"]
        self.access_key = kwargs["access_key"]
        self.secret_key = kwargs["secret_key"]
        self.certificate_validation = kwargs["certificate_validation"]
    
    def get_data_model(self, model):
        path = Path(f"{os.getcwd()}/pyturbot/pyturbot/data/{model}/service.yaml")
        if not path.exists():
            log.debug(f"Path: {path.as_posix}")
            log.error("Incorrect Data Model or Path")
            raise Exception ("Incorrect Data Model or Path")
        with open(path, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except Exception as e:
                log.error(f"Unable to open {path.as_posix()}")
                log.error(e)

    def configure(self, model):
        """
        Easy to remember name to initialize the data_model
        """
        self.service = self.get_data_model(model)
    
    def api(self, action=None, **kwargs):
        """
        """
        config = self.service[action]
        self.check_path_parameters(config, **kwargs)
        url = self.get_url(config, **kwargs)
        response = requests.request(
            config['method'],
            url,
            auth = HTTPBasicAuth(self.access_key, self.secret_key),
            verify=True,
            json=self.get_request_body(config, **kwargs),
            headers= {
                'content-type': "application/json",
                'cache-control': "no-cache"
            }
        )
        if response.status_code not in config['responses']:
            print(response.status_code)
            log.error("Unexpected HTTP response code", exc_info=True)
            raise Exception ("Unexpected HTTP response code")
        return response

    def get_url(self, config, **kwargs):
        """
        """
        api = config["api"].format(**kwargs)
        return f"https://{self.host}{api}"

    def check_path_parameters(self, config, **kwargs):
        """
        """
        missing_parameters = []
        for arg in config["path_params"]:
            if arg['name'] not in kwargs and arg['required'] == True:
                missing_parameters.append(arg)
        if len(missing_parameters) > 0:
            raise Exception (f"Required path parameters {missing_parameters} are missing")
    
    def get_request_body(self, config, **kwargs):
        """
        """
        if 'request_body' not in config:
            return json.loads({})
        request_body = {}
        for arg in config['request_body']:
            if arg['required']:
                if arg['name'] not in kwargs:
                    raise Exception (f"Required request body argument {arg['name']} is missing")
            if arg['name'] in kwargs:
                request_body[arg['name']] = kwargs[arg['name']]
        return request_body