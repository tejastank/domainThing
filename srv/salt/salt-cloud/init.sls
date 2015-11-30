include:
  - salt-cloud.cloud-map

apache-libcloud:
  pip.installed:
    - require:
      - pkg: python-pip

pycrypto:
  pip.installed:
    - require:
      - pkg: python-pip

salt-cloud:
  pkg.installed:
    - name: salt-cloud
    - require:
      - pip: apache-libcloud
      - pip: pycrypto

etc_salt_provider:
  file.managed:
    - name: /etc/salt/cloud.providers
    - template: jinja
    - source: salt://salt-cloud/cloud-providers.conf

etc_salt_profiles:
  file.managed:
    - name: /etc/salt/cloud.profiles.d/gen00.conf
    - template: jinja
    - source: salt://salt-cloud/cloud.profiles.d/gen00.conf
    - makedirs: True