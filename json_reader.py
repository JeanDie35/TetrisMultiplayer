import json

class JSONReader:

    config = {}

    def __init__(self):
        self.get_data()

    def save_file(self):
        with open("../config.json", "w") as file:
            file.write(json.dumps(self.config, indent=4))
            file.close()

    def get_data(self):
        with open("../config.json") as file:
            self.config = json.load(file)
            file.close()


