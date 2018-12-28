# Copyright 2017 The Armada Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

import falcon
from oslo_config import cfg
from oslo_log import log as logging

from armada import api
from armada.common import policy

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Status(api.BaseResource):

    @policy.enforce('tiller:get_status')
    def on_get(self, req, resp):
        '''
        get tiller status
        '''
        try:
            with self.get_tiller(req, resp) as tiller:

                LOG.debug(
                    'Tiller (Status) at: %s:%s, namespace=%s, '
                    'timeout=%s', tiller.tiller_host, tiller.tiller_port,
                    tiller.tiller_namespace, tiller.timeout)

                message = {
                    'tiller': {
                        'state': tiller.tiller_status(),
                        'version': tiller.tiller_version()
                    }
                }

                resp.status = falcon.HTTP_200
                resp.body = json.dumps(message)
                resp.content_type = 'application/json'

        except Exception as e:
            err_message = 'Failed to get Tiller Status: {}'.format(e)
            self.error(req.context, err_message)
            self.return_error(resp, falcon.HTTP_500, message=err_message)


class Release(api.BaseResource):

    @policy.enforce('tiller:get_release')
    def on_get(self, req, resp):
        '''Controller for listing Tiller releases.
        '''
        try:
            with self.get_tiller(req, resp) as tiller:

                LOG.debug(
                    'Tiller (Release) at: %s:%s, namespace=%s, '
                    'timeout=%s', tiller.tiller_host, tiller.tiller_port,
                    tiller.tiller_namespace, tiller.timeout)

                releases = {}
                for release in tiller.list_releases():
                    releases.setdefault(release.namespace, [])
                    releases[release.namespace].append(release.name)

                resp.body = json.dumps({'releases': releases})
                resp.content_type = 'application/json'
                resp.status = falcon.HTTP_200

        except Exception as e:
            err_message = 'Unable to find Tiller Releases: {}'.format(e)
            self.error(req.context, err_message)
            self.return_error(resp, falcon.HTTP_500, message=err_message)

    @policy.enforce('tiller:delete_release')
    def on_delete(self, req, resp, release):
        '''Controller for deleting Tiller release.
        '''
        purge = not req.get_param_as_bool('no_purge')
        try:
            with self.get_tiller(req, resp) as tiller:
                tiller.uninstall_release(release, purge)
                resp.body = json.dumps({
                    'message':
                    'Delete {} complete.'.format(release)
                })
                resp.content_type = 'application/json'
                resp.status = falcon.HTTP_200
        except Exception as e:
            err_message = 'Unable to delete Tiller Release: {}'.format(e)
            self.error(req.context, err_message)
            self.return_error(resp, falcon.HTTP_500, message=err_message)
