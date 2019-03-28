import logging

from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class DNSAbstractImporter(AbstractComponent):
    _name = 'dns.abstract.importer'
    _inherit = ['base.importer', 'base.dns.connector']
    _usage = 'dns.importer'

    def __init__(self, work_context):
        super(DNSAbstractImporter, self).__init__(work_context)
        self.domain_id = None
        self.external_id = None
        self.dns_record = None

    def _before_import(self):
        return

    def _after_import(self):
        return

    def _get_records(self, signal):
        """
        :param signal: Signal of the action
        """
        raise NotImplementedError

    def _validate_data(self, data):
        return

    def _map_data(self):
        return self.mapper.map_record(self.dns_record)

    def _get_binding(self, signal):
        return self.binder.to_internal(self.external_id)

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    def _create(self, data):
        """ Create the Odoo record """
        # special check on data before import
        self._validate_data(data)
        model = self.model.with_context(connector_no_export=True)
        binding = model.create(data)
        return binding

    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        self._validate_data(data)
        binding.with_context(no_connector_export=True).write(data)

    def run(self, domain_id, signal, record_id):
        self.domain_id = domain_id
        if record_id:
            self._run(record_id, signal)
        else:
            for _id in self.backend_adapter.search(domain_id):
                self._run(_id, signal)

    def _run(self, external_id, signal):
        self.external_id = external_id
        try:
            self.dns_record = self._get_records(signal)
        except Exception:
            return 'No response'

        binding = self._get_binding(signal)
        self._before_import()
        map_record = self._map_data()
        if binding:
            record = self._update_data(map_record)
            self._update(binding, record)
        else:
            record = self._create_data(map_record)
            binding = self._create(record)
        self.binder.bind(self.external_id, binding)
        self._after_import()
