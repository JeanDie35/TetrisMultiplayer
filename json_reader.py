import json
import os


class JSONReader:

    def __init__(self):
        self.get_data()

    def save_profiles(self):
        with open("../profiles.json", "w") as file:
            file.write(json.dumps(self.profiles, indent=4))
            file.close()


    def get_data(self):
        with open("../config.json", "r") as file:
            self.__config = json.load(file)
            file.close()

        if not os.path.isfile("../profiles.json"):
            # create a new file with a dico in it so that json reads smth in it
            self.save_profiles()

        with open("../profiles.json", "r") as file:
            self.profiles = json.load(file)
            file.close()
    @property
    def config(self):
        return self.__config
