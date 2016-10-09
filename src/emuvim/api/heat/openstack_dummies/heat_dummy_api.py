# -*- coding: UTF-8 -*-

from flask import request,jsonify, Response
from flask_restful import Api,Resource
import logging
import json
from emuvim.api.heat.resources import Stack
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
from datetime import datetime, timedelta
from emuvim.api.heat.heat_parser import HeatParser


compute = None
ip = None
port = None
class HeatDummyApi(BaseOpenstackDummy):

    def __init__(self, in_ip, in_port):
        global compute, ip, port
        super(HeatDummyApi, self).__init__(in_ip, in_port)
        compute = None
        ip = in_ip
        port = in_port
        self.api.add_resource(Shutdown, "/shutdown")
        self.api.add_resource(HeatListAPIVersions, "/")
        self.api.add_resource(HeatCreateStack, "/v1/<tenant_id>/stacks") # create Stack (post)  list stack (get)
        self.api.add_resource(HeatShowStack, "/v1/<tenant_id>/stacks/<stack_name_or_id>","/v1/<tenant_id>/stacks/<stack_name_or_id>/<stack_id>")
        self.api.add_resource(HeatUpdateStack, "/v1/<tenant_id>/stacks/<stack_name_or_id>","/v1/<tenant_id>/stacks/<stack_name_or_id>/<stack_id>")
        self.api.add_resource(HeatDeleteStack, "/v1/<tenant_id>/stacks/<stack_name_or_id>","/v1/<tenant_id>/stacks/<stack_name_or_id>/<stack_id>")

    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class Shutdown(Resource):
    def get(self):
        logging.debug(("%s is beeing shut doen") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

class HeatListAPIVersions(Resource):
    global ip, port

    def get(self):
        logging.debug("API CALL: Heat - List API Versions")
        resp = dict()

        resp['versions'] = dict()
        resp['versions'] = [{
                "status": "CURRENT",
                "id": "v1.0",
                "links": [
                    {
                        "href": "http://%s:%d/v2.0" % (ip, port),
                        "rel": "self"
                    }
                ]
            }]

        return Response(json.dumps(resp), status=200, mimetype="application/json")

class HeatCreateStack(Resource):
    global compute, ip, port
    def post(self, tenant_id):

        logging.debug("HEAT: Create Stack")

        try:
            stack_dict = request.json
            for stack in compute.stacks.values():
                if stack.stack_name == stack_dict['stack_name']:
                    return [], 409
            stack = Stack()
            stack.stack_name = stack_dict['stack_name']
            reader = HeatParser()
            if isinstance(stack_dict['template'], str) or isinstance(stack_dict['template'], unicode):
                stack_dict['template'] = json.loads(stack_dict['template'])
            if not reader.parse_input(stack_dict['template'], stack, compute.dc.label):
                return 'Could not create stack.', 400


            stack.creation_time = str(datetime.now())
            stack.status = "CREATE_COMPLETE"

            return_dict = {"stack": {"id": stack.id,
                                     "links": [
                                        {
                                            "href": "http://%s:%s/v1/%s/stacks/%s"
                                                    %(ip, port, tenant_id, stack.id),
                                            "rel": "self"
                                        } ]}}

            compute.add_stack(stack)
            compute.deploy_stack(stack.id)
            return Response(json.dumps(return_dict), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception("Heat: Create Stack exception.")
            return ex.message, 500

    def get(self, tenant_id):
        global compute

        logging.debug("HEAT: Stack List")
        try:
            return_stacks = dict()
            return_stacks['stacks'] = list()
            for stack in compute.stacks.values():
                return_stacks['stacks'].append(
                                {"creation_time": stack.creation_time,
                                  "description":"desc of "+stack.id,
                                  "id": stack.id,
                                  "links": [],
                                  "stack_name": stack.stack_name,
                                  "stack_status": stack.status,
                                  "stack_status_reason": "Stack CREATE completed successfully",
                                  "updated_time": stack.update_time,
                                  "tags": ""
                                })

            return Response(json.dumps(return_stacks), status=200, mimetype="application/json")
        except Exception as ex:
            logging.exception("Heat: List Stack exception.")
            return ex.message, 500

class HeatShowStack(Resource):
    def get(self, tenant_id, stack_name_or_id, stack_id=None):
        global compute, ip, port

        logging.debug("HEAT: Show Stack")
        try:
            stack = None
            if stack_name_or_id in compute.stacks:
                stack = compute.stacks[stack_name_or_id]
            else:
                for tmp_stack in compute.stacks.values():
                    if tmp_stack.stack_name == stack_name_or_id:
                        stack = tmp_stack
            if stack is None:
                return 'Could not resolve Stack - ID', 404

            return_stack = {
                            "stack": {
                                "capabilities": [],
                                "creation_time": stack.creation_time,
                                "description": "desc of "+stack.stack_name,
                                "disable_rollback": True,
                                "id": stack.id,
                                "links": [
                                    {
                                        "href": "http://%s:%s/v1/%s/stacks/%s"
                                                %(ip, port, tenant_id, stack.id),
                                        "rel": "self"
                                    }
                                ],
                                "notification_topics": [],
                                "outputs": [],
                                "parameters": {
                                    "OS::project_id": "3ab5b02f-a01f-4f95-afa1-e254afc4a435",  # add real project id
                                    "OS::stack_id": stack.id,
                                    "OS::stack_name": stack.stack_name
                                },
                                "stack_name": stack.stack_name,
                                "stack_owner": "The owner of the stack.",  # add stack owner
                                "stack_status": stack.status,
                                "stack_status_reason": "The reason for the current status of the stack.",  # add status reason
                                "template_description": "The description of the stack template.",
                                "stack_user_project_id": "The project UUID of the stack user.",
                                "timeout_mins": "",
                                "updated_time": "",
                                "parent": "",
                                "tags": ""
                            }
                        }

            return Response(json.dumps(return_stack), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception("Heat: Show stack exception.")
            return ex.message, 500

class HeatUpdateStack(Resource):
    def put(self, tenant_id, stack_name_or_id, stack_id=None):
        global compute, ip, port

        logging.debug("Heat: Update Stack")
        try:
            old_stack = None
            if stack_name_or_id in compute.stacks:
                old_stack = compute.stacks[stack_name_or_id]
            else:
                for tmp_stack in compute.stacks.values():
                    if tmp_stack.stack_name == stack_name_or_id:
                        old_stack = tmp_stack
            if old_stack is None:
                return 'Could not resolve Stack - ID', 404

            stack_dict = request.json

            stack = Stack()
            stack.stack_name = old_stack.stack_name
            stack.id = old_stack.id
            stack.creation_time = old_stack.creation_time
            stack.update_time = str(datetime.now())
            stack.status = "UPDATE_COMPLETE"

            reader = HeatParser()
            if isinstance(stack_dict['template'], str) or isinstance(stack_dict['template'], unicode):
                stack_dict['template'] = json.loads(stack_dict['template'])
            if not reader.parse_input(stack_dict['template'], stack, compute.dc.label):
                return 'Could not create stack.', 400

            if not compute.update_stack(old_stack.id, stack):
                return 'Could not update stack.', 400

            return Response(status=202, mimetype="application/json")

        except Exception as ex:
            logging.exception("Heat: Update Stack exception")
            return ex.message, 500

class HeatDeleteStack(Resource):
    def delete(self, tenant_id, stack_name_or_id, stack_id=None):
        global compute, ip, port

        logging.debug("Heat: Delete Stack")
        try:
            if stack_name_or_id in compute.stacks:
                compute.delete_stack(stack_name_or_id)
                return Response('Deleted Stack: ' + stack_name_or_id, 204)

            for stack in compute.stacks.values():
                if stack.stack_name == stack_name_or_id:
                    compute.delete_stack(stack.id)
                    return Response('Deleted Stack: ' + stack_name_or_id, 204)

        except Exception as ex:
            logging.exception("Heat: Delete Stack exception")
            return ex.message, 500
