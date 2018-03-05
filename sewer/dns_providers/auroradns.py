# DNS Provider for AuroRa DNS from the dutch hosting provider pcextreme
# https://www.pcextreme.nl/aurora/dns
# Aurora uses libcloud from apache
# https://libcloud.apache.org/

from libcloud.dns.providers import get_driver
from libcloud.dns.types import Provider, RecordType
import tldextract
from . import common


class AuroraDns(common.BaseDns):
    """
    Todo: re-organize this class so that we make it easier to mock things out to
    facilitate better tests.
    """
    dns_provider_name = 'aurora'

    def __init__(self, AURORA_API_KEY, AURORA_SECRET_KEY):

        self.AURORA_API_KEY = AURORA_API_KEY
        self.AURORA_SECRET_KEY = AURORA_SECRET_KEY
        super(AuroraDns, self).__init__()

    def create_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        self.logger.info('create_dns_record')
        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip('*.')

        # delete any prior existing DNS authorizations that may exist already
        self.delete_dns_record(
            domain_name=domain_name,
            base64_of_acme_keyauthorization=base64_of_acme_keyauthorization)

        extractedDomain = tldextract.extract(domain_name)
        domainSuffix = extractedDomain.domain + '.' + extractedDomain.suffix

        if extractedDomain.subdomain is '':
            subDomain = '_acme-challenge'
        else:
            subDomain = '_acme-challenge.' + extractedDomain.subdomain

        cls = get_driver(Provider.AURORADNS)
        driver = cls(key=self.AURORA_API_KEY, secret=self.AURORA_SECRET_KEY)
        zone = driver.get_zone(domainSuffix)
        zone.create_record(
            name=subDomain,
            type=RecordType.TXT,
            data=base64_of_acme_keyauthorization)
        return

    def delete_dns_record(self, domain_name, base64_of_acme_keyauthorization):
        self.logger.info('delete_dns_record')

        extractedDomain = tldextract.extract(domain_name)
        domainSuffix = extractedDomain.domain + '.' + extractedDomain.suffix

        if extractedDomain.subdomain is '':
            subDomain = '_acme-challenge'
        else:
            subDomain = '_acme-challenge.' + extractedDomain.subdomain

        cls = get_driver(Provider.AURORADNS)
        driver = cls(key=self.AURORA_API_KEY, secret=self.AURORA_SECRET_KEY)
        zone = driver.get_zone(domainSuffix)

        records = driver.list_records(zone)
        for x in records:
            if x.name == subDomain and x.type == 'TXT':
                record_id = x.id
                self.logger.info(
                    'Found record ' +
                    subDomain +
                    '.' +
                    domainSuffix +
                    ' with id : ' +
                    record_id +
                    '.')
                record = driver.get_record(
                    zone_id=zone.id, record_id=record_id)
                driver.delete_record(record)
                self.logger.info(
                    'Deleted record ' +
                    subDomain +
                    '.' +
                    domainSuffix +
                    ' with id : ' +
                    record_id +
                    '.')
            else:
                self.logger.info('Record ' + subDomain + '.' + domainSuffix +
                                 ' not found. No record to delete.')

        return
