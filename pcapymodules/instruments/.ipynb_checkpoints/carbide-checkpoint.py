import requests as rq

'''
If not available: Install by running the following command.
conda install requests
'''

class Carbide:
    def __init__(self, ip = '10.1.251.1', port =20018, version = 1):
        self.url = r'http://{0}:{1}/v{2}'.format(ip,port,version)
        
    def get(self, parameter, endpoint = 'Basic'):
        code = '{0}/{1}/{2}'.format(self.url, endpoint, parameter)
        response = rq.get(code)
        return response.json()
    
    def put(self, value, parameter, endpoint = 'Basic'):
        code = '{0}/{1}/{2}'.format(self.url, endpoint, parameter)
        response = rq.put(code, json = value)
        response1 = rq.get(code)
        return response1.json()
    
    def enable(self):
        code = '{0}/{1}/{2}'.format(self.url, 'Basic', 'EnableOutput')
        response = rq.post(code)
        return response.json()
    
    def disable(self):
        code = '{0}/{1}/{2}'.format(self.url, 'Basic', 'CloseOutput')
        response = rq.post(code)
        return response.json()
    
    @property
    def attenuator_percentage(self):
        return self.get('TargetAttenuatorPercentage', 'Basic')
    
    @attenuator_percentage.setter
    def attenuator_percentage(self, value):
        return self.put(value, 'TargetAttenuatorPercentage', 'Basic')
    
    @property
    def actual_output_energy(self):
        return self.get('ActualOutputEnergy', 'Basic')
    
    @property
    def actual_output_frequency(self):
        return self.get('ActualOutputFrequency', 'Basic')
    
    @property
    def actual_output_power(self):
        return self.get('ActualOutputPower', 'Basic')
