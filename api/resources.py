import falcon
from scripts.deploy import deploy

# route /deploy
class DeployResource:
    def on_post(self, req, resp):
        body = req.media

        for needed_field in ["revision", "fqdn"]:
            if needed_field not in body:
                resp.status = falcon.HTTP_400
                return

        deploy(req.context.repo_name, body["revision"], body["fqdn"], req.context.env)
        resp.status = falcon.HTTP_200