from conan import ConanFile
from conan.tools.scm import Git


class ConanRepo(ConanFile):
    name = "hello"
    version = "0.1"

    def export(self):
        git = Git(self, self.recipe_folder)
        git.coordinates_to_conandata()

    def source(self):
        git = Git(self)
        git.checkout_from_conandata_coordinates()

    def build(self):
        pass

    def package(self):
        pass
