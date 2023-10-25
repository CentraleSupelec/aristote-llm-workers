from git.config import GitConfigParser
from jinja2.environment import Environment
from jinja2.ext import Extension
from slugify import slugify


class SlugifyExtension(Extension):
    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        environment.filters["slugify"] = slugify


class GitAuthorExtension(Extension):
    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        git_config = GitConfigParser()
        environment.globals["git_user_name"] = git_config.get_value("user", "name", default="")
        environment.globals["git_user_mail"] = git_config.get_value("user", "email", default="")
