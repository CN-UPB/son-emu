from flask_restful import Resource
from flask import Response, request
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
import logging
import json
import uuid
from mininet.link import Link


class NovaDummyApi(BaseOpenstackDummy):
    def __init__(self, in_ip, in_port, compute):
        super(NovaDummyApi, self).__init__(in_ip, in_port)
        self.compute = compute

        self.api.add_resource(NovaVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(Shutdown, "/shutdown")
        self.api.add_resource(NovaVersionShow, "/v2.1/<id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListServersApi, "/v2.1/<id>/servers",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListServersDetailed, "/v2.1/<id>/servers/detail",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaShowServerDetails, "/v2.1/<id>/servers/<serverid>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaInterfaceToServer, "/v2.1/<id>/servers/<serverid>/os-interface",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaShowAndDeleteInterfaceAtServer, "/v2.1/<id>/servers/<serverid>/os-interface/<portid>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListFlavors, "/v2.1/<id>/flavors",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListFlavorsDetails, "/v2.1/<id>/flavors/detail",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListFlavorById, "/v2.1/<id>/flavors/<flavorid>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListImages, "/v2.1/<id>/images",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListImagesDetails, "/v2.1/<id>/images/detail",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListImageById, "/v2.1/<id>/images/<imageid>",
                              resource_class_kwargs={'api': self})

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("NovaDummyApi", self.ip, self.port))
        # add some flavors for good measure
        self.compute.add_flavor('m1.tiny', 1, 512, "MB", 1, "GB")
        self.compute.add_flavor('m1.nano', 1, 64, "MB", 0, "GB")
        self.compute.add_flavor('m1.micro', 1, 128, "MB", 0, "GB")
        self.compute.add_flavor('m1.small', 1, 1024, "MB", 2, "GB")
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class Shutdown(Resource):
    def get(self):
        logging.debug(("%s is beeing shut doen") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


class NovaVersionsList(Resource):
    def __init__(self, api):
        self.api = api

    def get(self):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = """
                {
                    "versions": [
                        {
                            "id": "v2.1",
                            "links": [
                                {
                                    "href": "http://%s:%d/v2.1/",
                                    "rel": "self"
                                }
                            ],
                            "status": "CURRENT",
                            "version": "2.38",
                            "min_version": "2.1",
                            "updated": "2013-07-23T11:33:21Z"
                        }
                    ]
                }
            """ % (self.api.ip, self.api.port)

            return Response(resp, status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not show list of versions." % __name__)
            return ex.message, 500


class NovaVersionShow(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = """
            {
                "version": {
                    "id": "v2.1",
                    "links": [
                        {
                            "href": "http://%s:%d/v2.1/",
                            "rel": "self"
                        },
                        {
                            "href": "http://docs.openstack.org/",
                            "rel": "describedby",
                            "type": "text/html"
                        }
                    ],
                    "media-types": [
                        {
                            "base": "application/json",
                            "type": "application/vnd.openstack.compute+json;version=2.1"
                        }
                    ],
                    "status": "CURRENT",
                    "version": "2.38",
                    "min_version": "2.1",
                    "updated": "2013-07-23T11:33:21Z"
                }
            }
            """ % (self.api.ip, self.api.port)

            return Response(resp, status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not show list of versions." % __name__)
            return ex.message, 500


class NovaListServersApi(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['servers'] = list()
            for server in self.api.compute.computeUnits.values():
                s = server.create_server_dict(self.api.compute)
                s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (self.api.ip,
                                                                            self.api.port,
                                                                            id,
                                                                            server.id)}]

                resp['servers'].append(s)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500

    def post(self, id):
        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))
        '''
        Creates a server instance
        :param id: tenant id
        :return:
        '''
        try:
            server_dict = json.loads(request.data)['server']
            networks = server_dict.get('networks', None)
            name = str(self.api.compute.dc.label) + "_man_" + server_dict["name"][0:12]

            if self.api.compute.find_server_by_name_or_id(name) is not None:
                return Response("Server with name %s already exists." % name, status=409)
            # TODO: not finished!
            resp = dict()

            server = self.api.compute.create_server(name)
            server.full_name = str(self.api.compute.dc.label) + "_man_" + server_dict["name"]

            for flavor in self.api.compute.flavors.values():
                if flavor.id == server_dict.get('flavorRef', ''):
                     server.flavor = flavor.name
            for image in self.api.compute.images.values():
                if image.id == server_dict['imageRef']:
                    server.image = image.name

            if networks is not None:
                for net in networks:
                    port = self.api.compute.find_port_by_name_or_id(net.get('port', ""))
                    if port is not None:
                        server.port_names.append(port.name)
                    else:
                        return Response("Currently only networking by port is supported.", status=400)

            self.api.compute._start_compute(server)

            return NovaShowServerDetails(self.api).get(id, server.id)

        except Exception as ex:
            logging.exception(u"%s: Could not create the server." % __name__)
            return ex.message, 500


class NovaListServersDetailed(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = {"servers": list()}
            for server in self.api.compute.computeUnits.values():
                s = server.create_server_dict(self.api.compute)
                s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (self.api.ip,
                                                                            self.api.port,
                                                                            id,
                                                                            server.id)}]
                flavor = self.api.compute.flavors[server.flavor]
                s['flavor'] = {
                    "id": flavor.id,
                    "links": [
                        {
                            "href": "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                         self.api.port,
                                                                         id,
                                                                         flavor.id),
                            "rel": "bookmark"
                        }
                    ]
                }
                image = self.api.compute.images[server.image]
                s['image'] = {
                    "id": image.id,
                    "links": [
                        {
                            "href": "http://%s:%d/v2.1/%s/images/%s" % (self.api.ip,
                                                                        self.api.port,
                                                                        id,
                                                                        image.id),
                            "rel": "bookmark"
                        }
                    ]
                }

                resp['servers'].append(s)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500


class NovaListFlavors(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['flavors'] = list()
            for flavor in self.api.compute.flavors.values():
                f = flavor.__dict__.copy()
                f['id'] = flavor.id
                f['name'] = flavor.name
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                            self.api.port,
                                                                            id,
                                                                            flavor.id)}]
                resp['flavors'].append(f)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500

    def post(self, id):
        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))
        data = json.loads(request.data).get("flavor")
        logging.warning("Create Flavor: %s" % str(data))
        # add to internal dict
        f = self.api.compute.add_flavor(
            data.get("name"),
            data.get("vcpus"),
            data.get("ram"), "MB",
            data.get("disk"), "GB")
        # create response based on incoming data
        data["id"] = f.id
        data["links"] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                       self.api.port,
                                                                       id,
                                                                       f.id)}]
        resp = {"flavor": data}
        return Response(json.dumps(resp), status=200, mimetype="application/json")


class NovaListFlavorsDetails(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['flavors'] = list()
            for flavor in self.api.compute.flavors.values():
                # use the class dict. it should work fine
                # but use a copy so we don't modifiy the original
                f = flavor.__dict__.copy()
                # add additional expected stuff stay openstack compatible
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                            self.api.port,
                                                                            id,
                                                                            flavor.id)}]
                f['OS-FLV-DISABLED:disabled'] = False
                f['OS-FLV-EXT-DATA:ephemeral'] = 0
                f['os-flavor-access:is_public'] = True
                f['ram'] = flavor.memory
                f['vcpus'] = flavor.cpu
                f['swap'] = 0
                f['disk'] = flavor.storage
                f['rxtx_factor'] = 1.0
                resp['flavors'].append(f)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500

    def post(self, id):
        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))
        data = json.loads(request.data).get("flavor")
        logging.warning("Create Flavor: %s" % str(data))
        # add to internal dict
        f = self.api.compute.add_flavor(
            data.get("name"),
            data.get("vcpus"),
            data.get("ram"), "MB",
            data.get("disk"), "GB")
        # create response based on incoming data
        data["id"] = f.id
        data["links"] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                       self.api.port,
                                                                       id,
                                                                       f.id)}]
        resp = {"flavor": data}
        return Response(json.dumps(resp), status=200, mimetype="application/json")


class NovaListFlavorById(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id, flavorid):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['flavor'] = dict()
            flavor = self.api.compute.flavors.get(flavorid, None)
            if flavor is None:
                for f in self.api.compute.flavors.values():
                    if f.id == flavorid:
                        flavor = f
                        break
            resp['flavor']['id'] = flavor.id
            resp['flavor']['name'] = flavor.name
            resp['flavor']['links'] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                                     self.api.port,
                                                                                     id,
                                                                                     flavor.id)}]
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve flavor with id %s" % (__name__, flavorid))
            return ex.message, 500


class NovaListImages(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['images'] = list()
            for image in self.api.compute.images.values():
                f = dict()
                f['id'] = image.id
                f['name'] = str(image.name).replace(":latest", "")
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/images/%s" % (self.api.ip,
                                                                           self.api.port,
                                                                           id,
                                                                           image.id)}]
                resp['images'].append(f)
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of images." % __name__)
            return ex.message, 500


class NovaListImagesDetails(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['images'] = list()
            for image in self.api.compute.images.values():
                # use the class dict. it should work fine
                # but use a copy so we don't modifiy the original
                f = image.__dict__.copy()
                # add additional expected stuff stay openstack compatible
                f['name'] = str(image.name).replace(":latest", "")
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/images/%s" % (self.api.ip,
                                                                           self.api.port,
                                                                           id,
                                                                           image.id)}]
                f['metadata'] = {
                    "architecture": "x86_64",
                    "auto_disk_config": "True",
                    "kernel_id": "nokernel",
                    "ramdisk_id": "nokernel"
                }
                resp['images'].append(f)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of images." % __name__)
            return ex.message, 500


class NovaListImageById(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id, imageid):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        '''
        Gets an image by id from the emulator with openstack nova compliant return values.
        :param id: tenantid, we ignore this most of the time
        :param imageid: id of the image. If it is 1 the dummy CREATE-IMAGE is returned
        :return:
        '''
        try:
            resp = dict()
            i = resp['image'] = dict()
            for image in self.api.compute.images.values():
                if image.id == imageid or image.name == imageid:
                    i['id'] = image.id
                    i['name'] = image.name

                    return Response(json.dumps(resp), status=200, mimetype="application/json")

            return Response("Image with id or name %s does not exists." % imageid, status=404)

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve image with id %s." % (__name__, imageid))
            return ex.message, 500


class NovaShowServerDetails(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id, serverid):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            server = self.api.compute.find_server_by_name_or_id(serverid)
            if server is None:
                return Response("Server with id or name %s does not exists." % serverid, status=404)
            s = server.create_server_dict()
            s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (self.api.ip,
                                                                        self.api.port,
                                                                        id,
                                                                        server.id)}]

            flavor = self.api.compute.flavors[server.flavor]
            s['flavor'] = {
                "id": flavor.id,
                "links": [
                    {
                        "href": "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                     self.api.port,
                                                                     id,
                                                                     flavor.id),
                        "rel": "bookmark"
                    }
                ]
            }
            image = self.api.compute.images[server.image]
            s['image'] = {
                "id": image.id,
                "links": [
                    {
                        "href": "http://%s:%d/v2.1/%s/images/%s" % (self.api.ip,
                                                                    self.api.port,
                                                                    id,
                                                                    image.id),
                        "rel": "bookmark"
                    }
                ]
            }

            return Response(json.dumps({'server': s}), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the server details." % __name__)
            return ex.message, 500


class NovaInterfaceToServer(Resource):
    def __init__(self, api):
        self.api = api

    def post(self, id, serverid):
        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))
        try:
            server = self.api.compute.find_server_by_name_or_id(serverid)
            if server is None:
                return Response("Server with id or name %s does not exists." % serverid, status=404)
            data = json.loads(request.data).get("interfaceAttachment")
            resp = dict()
            port = data.get("port_id", None)
            net = data.get("net_id", None)
            dc = self.api.compute.dc
            network_dict = dict()
            network = None


            if net is not None and port is not None:
                network_dict['id'] = port.intf_name
                network_dict['ip'] = port.ip_address
                network_dict[network_dict['id']] = network.name
            elif net is not None:
                network = self.api.compute.find_network_by_name_or_id(net)
                if network is None:
                    return Response("Network with id or name %s does not exists." % net, status=404)
                port = self.api.compute.create_port("port:cp%s:fl:%s" %
                                                    (len(self.api.compute.ports), str(uuid.uuid4())))

                port.net_name = network.name
                port.ip_address = network.get_new_ip_address(port.name)
                network_dict['id'] = port.intf_name
                network_dict['ip'] = port.ip_address
                network_dict[network_dict['id']] = network.name
            elif port is not None:
                port = self.api.compute.find_port_by_name_or_id(port)
                network_dict['id'] = port.intf_name
                network_dict['ip'] = port.ip_address
                network = self.api.compute.find_network_by_name_or_id(port.net_name)
                network_dict[network_dict['id']] = network.name
            else:
                raise Exception("You can only attach interfaces by port or network at the moment")

            if network == self.api.manage.floating_network:
                self.api.manage.floating_switch.dpctl("add-flow", 'cookie=1,actions=NORMAL')
                dc.net.addLink(server.emulator_compute, self.api.manage.floating_switch,
                               params1=network_dict, cls=Link, intfName1=port.intf_name)

                # if we want to have exclusive host-to-n connections we have to enable this
                # link_dict = dc.net.DCNetwork_graph[server.name][self.api.manage.floating_switch]
                # for link in link_dict:
                #     if link_dict[link]['src_port_name'] == port.intf_name:
                #         inport = int(link_dict[link]['dst_port_nr'])

                # connect each VNF to the host only. No pinging between VNFs possible
                # self.api.manage.floating_switch("add-flow", "in_port=%s,actions=OUTPUT:1" % inport)
            else:
                dc.net.addLink(server.emulator_compute, dc.switch,
                               params1=network_dict, cls=Link, intfName1=port.intf_name)
            resp["port_state"] = "ACTIVE"
            resp["port_id"] = port.id
            resp["net_id"] = self.api.compute.find_network_by_name_or_id(port.net_name).id
            resp["mac_addr"] = port.mac_address
            resp["fixed_ips"] = list()
            fixed_ips = dict()
            fixed_ips["ip_address"] = port.ip_address
            fixed_ips["subnet_id"] = network.subnet_name
            resp["fixed_ips"].append(fixed_ips)
            return Response(json.dumps({"interfaceAttachment": resp}), status=202, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not add interface to the server." % __name__)
            return ex.message, 500


class NovaShowAndDeleteInterfaceAtServer(Resource):
    def __init__(self, api):
        self.api = api

    def delete(self, id, serverid, port_id):
        logging.debug("API CALL: %s DELETE" % str(self.__class__.__name__))
        try:
            server = self.api.compute.find_server_by_name_or_id(serverid)
            if server is None:
                return Response("Server with id or name %s does not exists." % serverid, status=404)
            port = self.api.compute.find_port_by_name_or_id(port_id)
            if port is None:
                return Response("Port with id or name %s does not exists." % port_id, status=404)

            for link in self.api.compute.dc.net.links:
                if str(link.intf1) == port.intf_name and \
                                str(link.intf1.ip) == port.ip_address.split('/')[0]:
                    self.api.compute.dc._remove_link(link.intf1.node.name, link)
                    break

            if self.api.manage.get_flow_group(server.name, port.intf_name) is not None:
                self.api.manage.delete_loadbalancer(server.name, port.intf_name)

            return Response("", status=202, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not detach interface to the server." % __name__)
            return ex.message, 500
